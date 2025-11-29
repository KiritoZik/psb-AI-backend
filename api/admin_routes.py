"""
Роуты для админа (защищенные эндпоинты)
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import timedelta, timezone
from datetime import datetime as dt
from typing import Optional

from db.session import get_db
from schemas.auth import LoginRequest, Token
from schemas.letter import (
    LetterDetailResponse,
    LetterListResponse,
    LetterEditRequest,
    LetterApprovalRequest
)
from schemas.history import HistoryResponse, HistoryItem
from models.letter import Letter, LetterStatus, LetterUrgency
from services.auth import authenticate_admin, create_access_token, get_current_admin
from services.email_sender import EmailSender
from core.config import settings

router = APIRouter()


@router.post("/auth/login", response_model=Token)
async def login(login_request: LoginRequest):
    """
    Эндпоинт для авторизации админа.
    Принимает логин и пароль, возвращает JWT токен.
    """
    if not authenticate_admin(login_request.username, login_request.password):
        raise HTTPException(
            status_code=401,
            detail="Неверный логин или пароль"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": login_request.username},
        expires_delta=access_token_expires
    )
    
    return Token(access_token=access_token, token_type="bearer")


@router.get("/letters", response_model=LetterListResponse)
async def get_all_letters(
    skip: int = Query(0, ge=0, description="Количество записей для пропуска"),
    limit: int = Query(100, ge=1, le=1000, description="Максимальное количество записей"),
    status: Optional[str] = Query(None, description="Фильтр по статусу"),
    urgency: Optional[str] = Query(None, description="Фильтр по срочности"),
    sort_by: str = Query("urgency", description="Сортировка: urgency, received_date, deadline"),
    sort_order: str = Query("desc", description="Порядок сортировки: asc, desc"),
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    """
    Получает список всех писем с возможностью фильтрации и сортировки.
    Требует авторизации админа.
    
    - **status**: pending_approval, approved, sent
    - **urgency**: low, medium, high
    - **sort_by**: urgency (по умолчанию), received_date, deadline
    - **sort_order**: desc (по умолчанию), asc
    """
    try:
        query = db.query(Letter)
        
        if status:
            try:
                status_enum = LetterStatus(status)
                query = query.filter(Letter.status == status_enum)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Неверный статус. Доступные статусы: {[s.value for s in LetterStatus]}"
                )
        
        if urgency:
            try:
                urgency_enum = LetterUrgency(urgency)
                query = query.filter(Letter.urgency == urgency_enum)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Неверная срочность. Доступные значения: {[u.value for u in LetterUrgency]}"
                )
        
        urgency_order = {
            LetterUrgency.HIGH: 0,
            LetterUrgency.MEDIUM: 1,
            LetterUrgency.LOW: 2
        }
        
        if sort_by == "urgency":
            letters = query.all()
            if sort_order == "asc":
                letters.sort(key=lambda x: urgency_order.get(x.urgency, 999))
            else:
                letters.sort(key=lambda x: urgency_order.get(x.urgency, 999), reverse=True)
            total = len(letters)
            letters = letters[skip:skip + limit]
        elif sort_by == "received_date":
            if sort_order == "asc":
                query = query.order_by(Letter.received_date.asc())
            else:
                query = query.order_by(Letter.received_date.desc())
            total = query.count()
            letters = query.offset(skip).limit(limit).all()
        elif sort_by == "deadline":
            if sort_order == "asc":
                query = query.order_by(Letter.reply_deadline.asc())
            else:
                query = query.order_by(Letter.reply_deadline.desc())
            total = query.count()
            letters = query.offset(skip).limit(limit).all()
        else:
            raise HTTPException(
                status_code=400,
                detail="Неверное поле для сортировки. Используйте: urgency, received_date, deadline"
            )
        
        return LetterListResponse(
            items=[LetterDetailResponse.model_validate(letter) for letter in letters],
            total=total
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении списка писем: {str(e)}")


@router.get("/letters/{letter_id}", response_model=LetterDetailResponse)
async def get_letter(
    letter_id: int,
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    """
    Получает детальную информацию о письме по ID.
    Требует авторизации админа.
    """
    letter = db.query(Letter).filter(Letter.id == letter_id).first()
    
    if not letter:
        raise HTTPException(status_code=404, detail="Письмо не найдено")
    
    return LetterDetailResponse.model_validate(letter)


@router.put("/letters/{letter_id}/edit", response_model=LetterDetailResponse)
async def edit_letter_answer(
    letter_id: int,
    edit_request: LetterEditRequest,
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    """
    Редактирует ответ письма. Сохраняет отредактированный ответ.
    Требует авторизации админа.
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
async def approve_letter(
    letter_id: int,
    approval_request: LetterApprovalRequest,
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    """
    Одобряет письмо.
    Если одобрено и есть отредактированный ответ, сохраняет его.
    Требует авторизации админа.
    """
    try:
        letter = db.query(Letter).filter(Letter.id == letter_id).first()
        
        if not letter:
            raise HTTPException(status_code=404, detail="Письмо не найдено")
        
        if approval_request.approved:
            letter.status = LetterStatus.APPROVED
            if approval_request.edited_answer:
                letter.edited_answer = approval_request.edited_answer
        
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
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    """
    Отправляет одобренное письмо адресанту.
    Письмо должно быть одобрено (status=approved).
    Используется отредактированный ответ, если он есть, иначе сгенерированный.
    Требует авторизации админа.
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
        
        answer_to_send = letter.edited_answer or letter.generated_answer
        
        email_sender = EmailSender()
        await email_sender.send_email(
            to_email=letter.sender_email,
            to_name=letter.sender_name,
            subject="Ответ на ваше обращение",
            body=answer_to_send
        )
        
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


@router.get("/history", response_model=HistoryResponse)
async def get_history(
    skip: int = Query(0, ge=0, description="Количество записей для пропуска"),
    limit: int = Query(100, ge=1, le=1000, description="Максимальное количество записей"),
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    """
    Возвращает историю всех писем и ответов из базы данных.
    Требует авторизации админа.
    """
    try:
        query = db.query(Letter)
        total = query.count()
        letters = query.order_by(Letter.received_date.desc()).offset(skip).limit(limit).all()
        
        return HistoryResponse(
            items=[HistoryItem.model_validate(letter) for letter in letters],
            total=total
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при получении истории: {str(e)}"
        )

