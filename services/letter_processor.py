from datetime import datetime, timedelta, timezone
from typing import Optional

from generator import YandexGPTGenerator, get_generator, generate_reply
from models.letter import LetterStyle
from services.ml_classifier import get_ml_classifier
from services.field_extractor import FieldExtractor
from domain.letters import LetterType, to_letter_type, get_letter_style, get_reply_deadline_days


class LetterProcessor:
    """Сервис для обработки писем"""
    
    def __init__(self, generator: Optional[YandexGPTGenerator] = None):
        self.generator = generator or get_generator()
        self.field_extractor = FieldExtractor()
    
    def process_letter(
        self,
        text: str,
        sender_name: Optional[str] = None,
        letter_style: Optional[LetterStyle] = None,
        reply_deadline_days: Optional[int] = None
    ) -> dict:
        """
        Обрабатывает письмо: классифицирует, извлекает поля, генерирует ответ
        
        Args:
            text: Текст входящего письма
            sender_name: Имя адресанта (опционально)
            letter_style: Стиль письма (если не указан, определяется автоматически)
            reply_deadline_days: Количество дней до срока ответа (по умолчанию зависит от типа письма)
        
        Returns:
            dict с данными для сохранения в БД
        """
        ml_classifier = get_ml_classifier()
        classification_result = ml_classifier.classify(text)
        classification = classification_result["type"]
        letter_type: LetterType = to_letter_type(classification)
        classification_confidence = classification_result.get("confidence", 0.7)
        urgency = classification_result.get("urgency", "medium")
        tone = classification_result.get("tone", "formal")
        entities = classification_result.get("entities", {})
        
        fields = self.field_extractor.extract_all(text)
        
        if entities:
            if entities.get("dates"):
                fields["dates"] = list(set(fields.get("dates", []) + entities["dates"]))
            if entities.get("contract_numbers"):
                fields["contract_numbers"] = list(set(fields.get("contract_numbers", []) + entities["contract_numbers"]))
            if entities.get("names") and not fields.get("sender_name"):
                fields["sender_name"] = entities["names"][0] if entities["names"] else None
        
        if not sender_name and fields.get("sender_name"):
            sender_name = fields["sender_name"]
        
        if letter_style is None:
            letter_style = get_letter_style(letter_type)
        
        if reply_deadline_days is None:
            reply_deadline_days = get_reply_deadline_days(letter_type)
        
        received_date = datetime.now(timezone.utc)
        reply_deadline = received_date + timedelta(days=reply_deadline_days)
        
        generated_answer = generate_reply(
            text=text,
            classification=classification,
            fields=fields,
            generator=self.generator
        )
        
        return {
            "text": text,
            "generated_answer": generated_answer,
            "sender_name": sender_name,
            "letter_style": letter_style,
            "received_date": received_date,
            "reply_deadline": reply_deadline,
            "classification": classification,
            "classification_confidence": classification_confidence,
            "urgency": urgency,
            "tone": tone,
            "extracted_fields": fields
        }

