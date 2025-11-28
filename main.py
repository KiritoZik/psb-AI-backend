from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router
from db.session import engine, Base
from core.config import settings

# Импортируем модели для создания таблиц
from models import letter

# Создаем таблицы в базе данных
Base.metadata.create_all(bind=engine)

# Создаем приложение FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    description="Backend для обработки писем с использованием AI (YandexGPT)",
    version="1.0.0"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роуты
app.include_router(router, prefix="/api/v1", tags=["letters"])


@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "message": "PSB AI Backend API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Проверка здоровья приложения"""
    return {"status": "healthy"}

