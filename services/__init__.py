from .letter_processor import LetterProcessor
from .email_sender import EmailSender
from .field_extractor import FieldExtractor

# Опциональные ML импорты
try:
    from .ml_classifier import MLClassifier, get_ml_classifier
    ML_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    ML_AVAILABLE = False
    MLClassifier = None
    get_ml_classifier = None

__all__ = [
    "LetterProcessor",
    "EmailSender",
    "FieldExtractor",
]

if ML_AVAILABLE:
    __all__.extend(["MLClassifier", "get_ml_classifier"])
