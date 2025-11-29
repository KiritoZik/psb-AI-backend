from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import timezone, timedelta
from datetime import datetime as dt
from db.session import get_db
from schemas.letter import LetterRequest, LetterProcessResponse
from schemas.history import GenerateRequest, GenerateResponse
from services.letter_processor import LetterProcessor
from services.ml_classifier import get_ml_classifier
from services.generate_answer import generate_answer
from services.field_extractor import FieldExtractor
from domain.letters import LetterType, to_letter_type, get_reply_deadline_days, get_letter_style
from models.letter import Letter, LetterStatus, LetterUrgency, to_letter_urgency

router = APIRouter()


@router.post("/process-letter", response_model=LetterProcessResponse)
async def process_letter(
    letter_request: LetterRequest,
    db: Session = Depends(get_db)
):
    """
    Получает письмо через API, обрабатывает его через generator,
    генерирует ответ и сохраняет данные в базу данных со статусом pending_approval.
    
    Сохраняемые поля:
    - Дата получения письма
    - Имя адресанта
    - Email адресанта
    - Текст входящего письма
    - Стиль письма
    - Срок до которого надо отправить ответ
    - Сгенерированный ответ
    - Статус: pending_approval
    """
    try:
        processor = LetterProcessor()
        processed_data = processor.process_letter(
            text=letter_request.text,
            sender_name=letter_request.sender_name
        )
        
        sender_email = letter_request.sender_email
        if not sender_email and processed_data.get("extracted_fields", {}).get("email"):
            sender_email = processed_data["extracted_fields"]["email"]
        
        urgency_str = processed_data.get("urgency")
        urgency = to_letter_urgency(urgency_str)
        
        letter = Letter(
            received_date=processed_data["received_date"],
            sender_name=processed_data["sender_name"],
            sender_email=sender_email,
            original_text=letter_request.text,
            letter_style=processed_data["letter_style"],
            reply_deadline=processed_data["reply_deadline"],
            urgency=urgency,
            status=LetterStatus.PENDING_APPROVAL,
            generated_answer=processed_data["generated_answer"]
        )
        
        db.add(letter)
        db.commit()
        db.refresh(letter)
        
        return LetterProcessResponse(
            letter_id=letter.id,
            status=letter.status,
            generated_answer=letter.generated_answer,
            sender_name=letter.sender_name,
            sender_email=letter.sender_email,
            letter_style=letter.letter_style,
            received_date=letter.received_date,
            reply_deadline=letter.reply_deadline
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при обработке письма: {str(e)}"
        )


@router.post("/generate", response_model=GenerateResponse)
async def generate(
    request: GenerateRequest,
    db: Session = Depends(get_db)
):
    """
    Принимает письмо, вызывает AI и возвращает ответ.
    Сохраняет в историю.
    """
    try:
        ml_classifier = get_ml_classifier()
        classification_result = ml_classifier.classify(request.text)
        classification = classification_result["type"]
        letter_type: LetterType = to_letter_type(classification)
        confidence = classification_result.get("confidence", 0.7)
        
        field_extractor = FieldExtractor()
        fields = field_extractor.extract_all(request.text)
        
        if classification_result.get("entities"):
            entities = classification_result["entities"]
            if entities.get("dates"):
                fields["dates"] = list(set(fields.get("dates", []) + entities["dates"]))
            if entities.get("contract_numbers"):
                fields["contract_numbers"] = list(set(fields.get("contract_numbers", []) + entities["contract_numbers"]))
        
        generated_answer = generate_answer(
            text=request.text,
            classification=classification,
            fields=fields
        )
        
        reply_deadline_days = get_reply_deadline_days(letter_type)
        received_date = dt.now(timezone.utc)
        reply_deadline = received_date + timedelta(days=reply_deadline_days)
        letter_style = get_letter_style(letter_type)
        
        urgency_str = classification_result.get("urgency")
        urgency = to_letter_urgency(urgency_str)
        
        letter = Letter(
            received_date=received_date,
            sender_name=request.sender_name or fields.get("sender_name"),
            sender_email=request.sender_email or fields.get("email"),
            original_text=request.text,
            letter_style=letter_style,
            reply_deadline=reply_deadline,
            urgency=urgency,
            status=LetterStatus.PENDING_APPROVAL,
            generated_answer=generated_answer
        )
        
        db.add(letter)
        db.commit()
        db.refresh(letter)
        
        return GenerateResponse(
            id=letter.id,
            original_text=letter.original_text,
            generated_answer=letter.generated_answer,
            classification=classification,
            classification_confidence=confidence,
            received_date=letter.received_date,
            created_at=letter.created_at
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при генерации ответа: {str(e)}"
        )


