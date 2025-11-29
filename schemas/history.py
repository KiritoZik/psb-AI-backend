"""
Схемы для работы с историей писем
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from models.letter import LetterStatus


class GenerateRequest(BaseModel):
    """Схема запроса на генерацию ответа"""
    text: str = Field(..., description="Текст входящего письма", min_length=1)
    sender_name: Optional[str] = Field(None, max_length=255, description="Имя отправителя")
    sender_email: Optional[str] = Field(None, description="Email отправителя")


class GenerateResponse(BaseModel):
    """Схема ответа после генерации"""
    id: int
    original_text: str
    generated_answer: str
    classification: str
    classification_confidence: float
    received_date: datetime
    created_at: datetime


class HistoryItem(BaseModel):
    """Элемент истории письма"""
    id: int
    received_date: datetime
    sender_name: Optional[str]
    sender_email: Optional[str]
    original_text: str
    generated_answer: str
    status: LetterStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class HistoryResponse(BaseModel):
    """Схема ответа со списком истории"""
    items: list[HistoryItem]
    total: int

