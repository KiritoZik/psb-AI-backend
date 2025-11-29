from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: str = "sqlite:///./letters.db"
    
    # Yandex Cloud LLM settings
    YANDEX_API_KEY: Optional[str] = None
    YANDEX_FOLDER_ID: Optional[str] = None
    YANDEX_MODEL_URI: Optional[str] = None
    
    # Email settings
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: Optional[str] = None
    SMTP_FROM_NAME: str = "PSB Bank"
    SMTP_USE_TLS: bool = True
    
    # Admin settings - ОБЯЗАТЕЛЬНО из .env файла
    ADMIN_PASSWORD: str = Field(..., description="Пароль администратора из .env файла")
    
    # JWT settings
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # Application settings
    APP_NAME: str = "PSB AI Backend"
    DEBUG: bool = False
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()

# Проверка что пароль загружен из .env
if not settings.ADMIN_PASSWORD or settings.ADMIN_PASSWORD == "":
    raise ValueError(
        "ADMIN_PASSWORD должен быть установлен в файле .env!\n"
        "Создайте файл .env в корне проекта и добавьте:\n"
        "ADMIN_PASSWORD=ваш-пароль"
    )

