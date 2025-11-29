from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router
from api.admin_routes import router as admin_router
from db.session import engine, Base
from core.config import settings
import logging
from models import letter

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def init_db():
    """Инициализация базы данных с обработкой ошибок"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✓ База данных инициализирована успешно")
    except Exception as e:
        logger.warning(f"⚠ Не удалось подключиться к базе данных: {e}")
        logger.warning("Приложение запустится, но функции работы с БД будут недоступны")
        logger.warning(f"Проверьте DATABASE_URL в .env (по умолчанию используется SQLite: sqlite:///./letters.db)")


def check_ml_availability():
    """Проверяет доступность ML компонентов при старте"""
    try:
        from services.ml_classifier import get_ml_classifier
        ml_classifier = get_ml_classifier()
        logger.info("✓ ML классификатор инициализирован успешно")
        return True
    except Exception as e:
        logger.error(f"✗ ML классификатор недоступен: {e}")
        logger.error("Приложение не сможет обрабатывать письма без ML моделей!")
        logger.error("Убедитесь, что:")
        logger.error("  1. Установлены зависимости: pip install joblib scikit-learn pandas pymorphy3")
        logger.error("  2. Обучены модели: запустите data_processing/training.py")
        logger.error("  3. Модели находятся в папке data_processing/models/")
        return False


app = FastAPI(
    title=settings.APP_NAME,
    description="Backend для обработки писем с использованием AI (YandexGPT) - ТОЛЬКО ML",
    version="1.0.0"
)

init_db()

ml_available = check_ml_availability()
if not ml_available:
    logger.warning("⚠ ВНИМАНИЕ: ML недоступен, обработка писем будет невозможна!")

# CORS middleware должен быть добавлен ДО роутеров
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",
        "http://127.0.0.1:4200",
        "http://localhost:58591",
        "http://127.0.0.1:58591",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(router, prefix="/api/v1", tags=["letters"])
app.include_router(admin_router, prefix="/api/v1/admin", tags=["admin"])


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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

