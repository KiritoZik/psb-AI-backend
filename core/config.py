from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/psb_ai_db"
    
    # Yandex Cloud LLM settings
    YANDEX_API_KEY: Optional[str] = None
    YANDEX_FOLDER_ID: Optional[str] = None
    YANDEX_MODEL_URI: Optional[str] = None
    
    # Application settings
    APP_NAME: str = "PSB AI Backend"
    DEBUG: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

