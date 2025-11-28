from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import timezone
from datetime import datetime as dt
from db.session import get_db
from schemas.letter import (
    LetterRequest, 
    LetterProcessResponse, 
    LetterEditRequest,
    LetterApprovalRequest,
    LetterDetailResponse,
    LetterListResponse
)
from services.letter_processor import LetterProcessor
from services.email_sender import EmailSender
from models.letter import Letter, LetterStatus

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
        # Создаем процессор писем
        processor = LetterProcessor()
        
        # Обрабатываем письмо (генерируем ответ)
        processed_data = processor.process_letter(
            text=letter_request.text,
            sender_name=letter_request.sender_name
        )
        
        # Сохраняем в базу данных
        letter = Letter(
            received_date=processed_data["received_date"],
            sender_name=processed_data["sender_name"],
            sender_email=letter_request.sender_email,
            original_text=letter_request.text,
            letter_style=processed_data["letter_style"],
            reply_deadline=processed_data["reply_deadline"],
            status=LetterStatus.PENDING_APPROVAL,  # По умолчанию ожидает одобрения
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


@router.get("/letters", response_model=LetterListResponse)
def get_letters(
    skip: int = Query(0, ge=0, description="Количество записей для пропуска"),
    limit: int = Query(100, ge=1, le=1000, description="Максимальное количество записей"),
    status: Optional[str] = Query(None, description="Фильтр по статусу"),
    db: Session = Depends(get_db)
):
    """
    Получает список писем с возможностью фильтрации по статусу.
    Полезно для получения писем ожидающих одобрения.
    """
    try:
        query = db.query(Letter)
        
        # Фильтрация по статусу
        if status:
            try:
                status_enum = LetterStatus(status)
                query = query.filter(Letter.status == status_enum)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Неверный статус. Доступные статусы: {[s.value for s in LetterStatus]}"
                )
        
        total = query.count()
        
        # Сортировка: сначала новые
        letters = query.order_by(Letter.received_date.desc()).offset(skip).limit(limit).all()
        
        return LetterListResponse(
            items=[LetterDetailResponse.model_validate(letter) for letter in letters],
            total=total
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении списка писем: {str(e)}")


@router.get("/letters/{letter_id}", response_model=LetterDetailResponse)
def get_letter(
    letter_id: int,
    db: Session = Depends(get_db)
):
    """
    Получает детальную информацию о письме по ID.
    """
    letter = db.query(Letter).filter(Letter.id == letter_id).first()
    
    if not letter:
        raise HTTPException(status_code=404, detail="Письмо не найдено")
    
    return LetterDetailResponse.model_validate(letter)


@router.put("/letters/{letter_id}/edit", response_model=LetterDetailResponse)
def edit_letter_answer(
    letter_id: int,
    edit_request: LetterEditRequest,
    db: Session = Depends(get_db)
):
    """
    Редактирует ответ письма. Сохраняет отредактированный ответ.
    """
    try:
        letter = db.query(Letter).filter(Letter.id == letter_id).first()
        
        if not letter:
            raise HTTPException(status_code=404, detail="Письмо не найдено")
        
        letter.edited_answer = edit_request.edited_answer
        
        db.commit()
        db.refresh(letter)
        
        return LetterDetailResponse.model_validate(letter)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при редактировании ответа: {str(e)}")


@router.post("/letters/{letter_id}/approve", response_model=LetterDetailResponse)
def approve_letter(
    letter_id: int,
    approval_request: LetterApprovalRequest,
    db: Session = Depends(get_db)
):
    """
    Одобряет или отклоняет письмо.
    Если одобрено и есть отредактированный ответ, сохраняет его.
    """
    try:
        letter = db.query(Letter).filter(Letter.id == letter_id).first()
        
        if not letter:
            raise HTTPException(status_code=404, detail="Письмо не найдено")
        
        if approval_request.approved:
            letter.status = LetterStatus.APPROVED
            # Если есть отредактированный ответ, сохраняем его
            if approval_request.edited_answer:
                letter.edited_answer = approval_request.edited_answer
        else:
            letter.status = LetterStatus.REJECTED
        
        db.commit()
        db.refresh(letter)
        
        return LetterDetailResponse.model_validate(letter)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при одобрении письма: {str(e)}")


@router.post("/letters/{letter_id}/send", response_model=LetterDetailResponse)
async def send_letter(
    letter_id: int,
    db: Session = Depends(get_db)
):
    """
    Отправляет одобренное письмо адресанту.
    Письмо должно быть одобрено (status=approved).
    Используется отредактированный ответ, если он есть, иначе сгенерированный.
    """
    try:
        letter = db.query(Letter).filter(Letter.id == letter_id).first()
        
        if not letter:
            raise HTTPException(status_code=404, detail="Письмо не найдено")
        
        if letter.status != LetterStatus.APPROVED:
            raise HTTPException(
                status_code=400,
                detail=f"Письмо должно быть одобрено для отправки. Текущий статус: {letter.status.value}"
            )
        
        if not letter.sender_email:
            raise HTTPException(
                status_code=400,
                detail="Не указан email адресанта для отправки ответа"
            )
        
        # Определяем какой ответ отправлять
        answer_to_send = letter.edited_answer or letter.generated_answer
        
        # Отправляем письмо
        email_sender = EmailSender()
        await email_sender.send_email(
            to_email=letter.sender_email,
            to_name=letter.sender_name,
            subject="Ответ на ваше обращение",
            body=answer_to_send
        )
        
        # Обновляем статус и дату отправки
        letter.status = LetterStatus.SENT
        letter.sent_date = dt.now(timezone.utc)
        
        db.commit()
        db.refresh(letter)
        
        return LetterDetailResponse.model_validate(letter)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при отправке письма: {str(e)}")
