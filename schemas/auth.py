"""
Схемы для аутентификации
"""

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Схема запроса на логин"""
    password: str = Field(..., description="Пароль администратора", min_length=3)


class Token(BaseModel):
    """Схема токена доступа"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Схема данных токена"""
    admin: bool = True

