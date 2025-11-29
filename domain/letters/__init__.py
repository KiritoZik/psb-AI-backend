"""
Доменный модуль для работы с письмами.

Содержит типы писем и чистые правила без привязки к FastAPI или БД.
"""

from .letter_types import (
    LetterType,
    to_letter_type,
    get_reply_deadline_days,
    get_letter_style,
)

__all__ = [
    "LetterType",
    "to_letter_type",
    "get_reply_deadline_days",
    "get_letter_style",
]


