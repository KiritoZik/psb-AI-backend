from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, Text, Enum as SQLEnum
from sqlalchemy.sql import func
from db.session import Base
import enum


class LetterStyle(str, enum.Enum):
    """Стиль письма"""
    FORMAL = "formal"  # Официальный
    INFORMAL = "informal"  # Неофициальный
    BUSINESS = "business"  # Деловой
    CASUAL = "casual"  # Непринужденный


class LetterUrgency(str, enum.Enum):
    """Срочность письма (соответствует ML‑модели: Low / Medium / High)"""
    LOW = "low"  # Низкая
    MEDIUM = "medium"  # Средняя
    HIGH = "high"  # Высокая


class LetterStatus(str, enum.Enum):
    """Статус обработки письма"""
    PENDING_APPROVAL = "pending_approval"  # Ожидает одобрения
    APPROVED = "approved"  # Одобрено
    SENT = "sent"  # Отправлено адресанту


class Letter(Base):
    __tablename__ = "letters"

    id = Column(Integer, primary_key=True, index=True)
    received_date = Column(DateTime(timezone=True), nullable=False, index=True, default=func.now())  # Дата получения письма
    sender_name = Column(String(255), nullable=True)  # Имя адресанта
    sender_email = Column(String(255), nullable=True, index=True)  # Email адресанта для отправки ответа
    original_text = Column(Text, nullable=False)  # Текст входящего письма
    letter_style = Column(SQLEnum(LetterStyle, native_enum=False), nullable=False)  # Стиль письма
    reply_deadline = Column(DateTime(timezone=True), nullable=False, index=True)  # Срок до которого надо отправить ответ
    urgency = Column(SQLEnum(LetterUrgency, native_enum=False), nullable=False, default=LetterUrgency.MEDIUM, index=True)  # Срочность письма
    
    # Статус обработки
    status = Column(SQLEnum(LetterStatus, native_enum=False), nullable=False, default=LetterStatus.PENDING_APPROVAL, index=True)
    
    # Ответы
    generated_answer = Column(Text, nullable=False)  # Сгенерированный ответ через AI
    edited_answer = Column(Text, nullable=True)  # Отредактированный ответ (после одобрения будет отправлен)
    
    # Дата отправки
    sent_date = Column(DateTime(timezone=True), nullable=True)  # Дата отправки ответа адресанту
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<Letter(id={self.id}, sender_name={self.sender_name}, status={self.status}, received_date={self.received_date})>"


def to_letter_urgency(raw: Optional[str]) -> LetterUrgency:
    """
    Безопасно конвертирует строковое значение (в т.ч. из ML‑модели) в LetterUrgency.

    ML‑классификатор сейчас возвращает три уровня срочности: Low / Medium / High.
    Функция нормализует регистр и подставляет MEDIUM по умолчанию для любых неизвестных значений.
    """
    if not raw:
        return LetterUrgency.MEDIUM

    norm = raw.strip().lower()
    mapping = {
        "low": LetterUrgency.LOW,
        "medium": LetterUrgency.MEDIUM,
        "high": LetterUrgency.HIGH,
    }

    return mapping.get(norm, LetterUrgency.MEDIUM)

