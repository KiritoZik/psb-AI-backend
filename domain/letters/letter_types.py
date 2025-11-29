"""
Определение типов писем и вспомогательные функции для работы с ними.

Типы полностью соответствуют значениям, которые возвращает ML‑модель.
"""

from enum import Enum

from models.letter import LetterStyle


class LetterType(str, Enum):
    """Типы писем (соответствуют типам из ML‑модели)"""

    OFFICIAL_COMPLAINT_OR_CLAIM = "Official Complaint or Claim"  # Официальная жалоба/претензия
    REGULATORY_REQUEST = "Regulatory Request"  # Регуляторный запрос
    PARTNERSHIP_PROPOSAL = "Partnership Proposal"  # Партнерское предложение
    INFORMATION_DOCUMENT_REQUEST = "Information/Document Request"  # Запрос информации/документов
    NOTIFICATION_OR_INFORMATION = "Notification or Information"  # Уведомление/информация
    APPROVAL_REQUEST = "Approval Request"  # Запрос на одобрение/согласование


def to_letter_type(classification: str) -> LetterType:
    """
    Безопасно конвертирует строковое значение из ML‑модели в LetterType.

    Если пришло неизвестное значение, возвращает APPROVAL_REQUEST как дефолт.
    """
    try:
        return LetterType(classification)
    except ValueError:
        return LetterType.APPROVAL_REQUEST


def get_reply_deadline_days(letter_type: LetterType) -> int:
    """
    Возвращает количество дней до дедлайна ответа в зависимости от типа письма.
    """
    mapping: dict[LetterType, int] = {
        LetterType.OFFICIAL_COMPLAINT_OR_CLAIM: 3,   # Жалобы требуют быстрого ответа
        LetterType.REGULATORY_REQUEST: 5,            # Регуляторные запросы – средний срок
        LetterType.INFORMATION_DOCUMENT_REQUEST: 7,  # Запросы документов – стандартный срок
        LetterType.PARTNERSHIP_PROPOSAL: 14,         # Партнёрские предложения – больше времени
        LetterType.NOTIFICATION_OR_INFORMATION: 1,   # Уведомления – быстрый ответ
        LetterType.APPROVAL_REQUEST: 7,              # Запросы на одобрение – стандартный срок
    }
    return mapping.get(letter_type, 7)


def get_letter_style(letter_type: LetterType) -> LetterStyle:
    """
    Определяет стиль письма (формальный / деловой) на основе типа письма.
    """
    if letter_type in (
        LetterType.OFFICIAL_COMPLAINT_OR_CLAIM,
        LetterType.REGULATORY_REQUEST,
    ):
        return LetterStyle.FORMAL

    if letter_type is LetterType.PARTNERSHIP_PROPOSAL:
        return LetterStyle.BUSINESS

    return LetterStyle.BUSINESS


__all__ = [
    "LetterType",
    "to_letter_type",
    "get_reply_deadline_days",
    "get_letter_style",
]


