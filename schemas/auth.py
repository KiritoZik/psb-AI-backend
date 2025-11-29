"""
Схемы для аутентификации
"""

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Схема запроса на логин"""
    username: str = Field(..., description="Логин пользователя", min_length=3)
    password: str = Field(..., description="Пароль пользователя", min_length=3)


class Token(BaseModel):
    """Схема токена доступа"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Схема данных токена"""
    username: str | None = None

