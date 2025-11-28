from datetime import datetime, timedelta
from typing import Optional
from generator.generator import YandexGPTGenerator, get_generator, generate_reply
from models.letter import LetterStyle


class LetterProcessor:
    """Сервис для обработки писем"""
    
    def __init__(self, generator: Optional[YandexGPTGenerator] = None):
        self.generator = generator or get_generator()
    
    def process_letter(
        self,
        text: str,
        sender_name: Optional[str] = None,
        letter_style: Optional[LetterStyle] = None,
        reply_deadline_days: Optional[int] = None
    ) -> dict:
        """
        Обрабатывает письмо: генерирует ответ и возвращает данные для сохранения
        
        Args:
            text: Текст входящего письма
            sender_name: Имя адресанта (опционально, можно извлечь из письма)
            letter_style: Стиль письма (если не указан, будет определен автоматически или по умолчанию)
            reply_deadline_days: Количество дней до срока ответа (по умолчанию 7)
        
        Returns:
            dict с данными для сохранения в БД
        """
        # Здесь будет код обработки для определения стиля и срока
        # Пока используем значения по умолчанию или переданные параметры
        
        if letter_style is None:
            # По умолчанию определяем как business
            letter_style = LetterStyle.BUSINESS
        
        if reply_deadline_days is None:
            reply_deadline_days = 7
        
        # Определяем дату получения (сейчас)
        from datetime import timezone
        received_date = datetime.now(timezone.utc)
        
        # Вычисляем срок ответа
        reply_deadline = received_date + timedelta(days=reply_deadline_days)
        
        # Генерируем ответ используя generator
        # Для генерации нужны classification и fields
        # Пока используем упрощенную версию
        classification = "general"  # Будет определено кодом обработки
        fields = {}  # Будет заполнено кодом обработки
        
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
            "reply_deadline": reply_deadline
        }

