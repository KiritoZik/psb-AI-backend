from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional
from models.letter import LetterStyle, LetterStatus


class LetterRequest(BaseModel):
    """Схема запроса на обработку письма"""
    text: str = Field(..., description="Текст входящего письма", min_length=1)
    sender_name: Optional[str] = Field(None, max_length=255, description="Имя адресанта")
    sender_email: Optional[EmailStr] = Field(None, description="Email адресанта для отправки ответа")


class LetterProcessResponse(BaseModel):
    """Схема ответа после обработки письма"""
    letter_id: int
    status: LetterStatus
    generated_answer: str
    sender_name: Optional[str]
    sender_email: Optional[str]
    letter_style: LetterStyle
    received_date: datetime
    reply_deadline: datetime


class LetterEditRequest(BaseModel):
    """Схема для редактирования ответа"""
    edited_answer: str = Field(..., description="Отредактированный ответ", min_length=1)


class LetterApprovalRequest(BaseModel):
    """Схема для одобрения/отклонения письма"""
    approved: bool = Field(..., description="Одобрить (True) или отклонить (False)")
    edited_answer: Optional[str] = Field(None, description="Отредактированный ответ (опционально)")


class LetterDetailResponse(BaseModel):
    """Схема ответа с детальной информацией о письме"""
    id: int
    received_date: datetime
    sender_name: Optional[str]
    sender_email: Optional[str]
    original_text: str
    letter_style: LetterStyle
    reply_deadline: datetime
    status: LetterStatus
    generated_answer: str
    edited_answer: Optional[str]
    sent_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LetterListResponse(BaseModel):
    """Схема ответа со списком писем"""
    items: list[LetterDetailResponse]
    total: int


class LetterResponse(BaseModel):
    """Схема ответа с информацией о письме (для обратной совместимости)"""
    id: int
    received_date: datetime
    sender_name: Optional[str]
    letter_style: LetterStyle
    reply_deadline: datetime
    status: LetterStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
