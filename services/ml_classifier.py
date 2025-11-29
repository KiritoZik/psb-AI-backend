"""
ML классификатор писем с использованием обученных моделей
ТОЛЬКО ML, без fallback - выбрасывает ошибки если ML недоступен
"""

import os
import sys
from pathlib import Path
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

data_processing_path = Path(__file__).parent.parent / "data_processing"
if data_processing_path.exists():
    sys.path.insert(0, str(data_processing_path.parent))

try:
    import joblib
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    joblib = None

try:
    if ML_AVAILABLE:
        data_processing_path = Path(__file__).parent.parent / "data_processing"
        if data_processing_path.exists():
            sys.path.insert(0, str(data_processing_path.parent))
            from data_processing.preprocessing import enhanced_preprocess_text, extract_entities
        else:
            enhanced_preprocess_text = None
            extract_entities = None
    else:
        enhanced_preprocess_text = None
        extract_entities = None
except ImportError:
    enhanced_preprocess_text = None
    extract_entities = None


class MLClassifier:
    """ML классификатор - ТОЛЬКО ML, без fallback"""
    
    def __init__(self, models_dir: Optional[str] = None):
        """
        Инициализация ML классификатора
        
        :param models_dir: Путь к папке с моделями (по умолчанию data_processing/models)
        :raises RuntimeError: Если ML зависимости или модели недоступны
        """
        self.models_dir = models_dir or str(Path(__file__).parent.parent / "data_processing" / "models")
        self.models = None
        self.hyperparams = None
        self.ml_available = False
        
        self._load_models()
    
    def _load_models(self):
        """Загружает обученные ML модели. Выбрасывает ошибку если недоступно."""
        if not ML_AVAILABLE or joblib is None:
            error_msg = (
                "ML зависимости не установлены. Установите: pip install joblib scikit-learn pandas pymorphy3"
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        if not os.path.exists(self.models_dir):
            error_msg = (
                f"Папка с моделями не найдена: {self.models_dir}\n"
                f"Обучите модели: запустите data_processing/training.py"
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        try:
            tasks = ['type', 'urgency', 'tone']
            models = {}
            missing_models = []
            
            for task_name in tasks:
                vectorizer_path = os.path.join(self.models_dir, f'vectorizer_{task_name}.pkl')
                classifier_path = os.path.join(self.models_dir, f'classifier_{task_name}.pkl')
                
                if os.path.exists(vectorizer_path) and os.path.exists(classifier_path):
                    vectorizer = joblib.load(vectorizer_path)
                    classifier = joblib.load(classifier_path)
                    models[task_name] = {
                        'vectorizer': vectorizer,
                        'classifier': classifier
                    }
                else:
                    missing_models.append(task_name)
            
            if missing_models:
                error_msg = (
                    f"Модели не найдены для задач: {', '.join(missing_models)}\n"
                    f"Ожидаемые файлы в {self.models_dir}:\n"
                    f"  - vectorizer_{missing_models[0]}.pkl и classifier_{missing_models[0]}.pkl\n"
                    f"Обучите модели: запустите data_processing/training.py"
                )
                logger.error(error_msg)
                raise RuntimeError(error_msg)
            
            self.models = models
            self.ml_available = True
            logger.info("✓ ML модели загружены успешно")
            
        except RuntimeError:
            raise
        except Exception as e:
            error_msg = (
                f"Ошибка загрузки ML моделей: {e}\n"
                f"Проверьте целостность файлов моделей в {self.models_dir}"
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
    
    def classify(self, text: str) -> Dict:
        """
        Классифицирует письмо используя ТОЛЬКО ML модели
        
        :param text: Текст письма
        :return: Словарь с классификацией
        :raises RuntimeError: Если ML модели не загружены или недоступны
        """
        if not self.ml_available or not self.models:
            error_msg = (
                "ML модели не загружены. Убедитесь, что:\n"
                f"1. Модели находятся в {self.models_dir}\n"
                f"2. Все необходимые файлы моделей присутствуют\n"
                f"3. Запустите data_processing/training.py для обучения моделей"
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        return self._classify_with_ml(text)
    
    def _classify_with_ml(self, text: str) -> Dict:
        """
        Классификация с использованием ML моделей
        
        :param text: Текст письма
        :return: Словарь с классификацией
        :raises RuntimeError: Если preprocessing функции недоступны или произошла ошибка
        """
        if enhanced_preprocess_text is None or extract_entities is None:
            error_msg = (
                "preprocessing функции недоступны. Убедитесь, что:\n"
                f"1. Модуль data_processing/preprocessing.py существует\n"
                f"2. Установлены зависимости: pip install pymorphy3"
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        try:
            classification = {}
            
            for task_name, model_data in self.models.items():
                # Предобработка текста
                processed_text = enhanced_preprocess_text(text, remove_personal_data_flag=True)
                
                # Векторизация
                vectorizer = model_data['vectorizer']
                text_vector = vectorizer.transform([processed_text])
                
                # Классификация
                classifier = model_data['classifier']
                prediction = classifier.predict(text_vector)[0]
                
                # Получаем вероятность (если доступна)
                if hasattr(classifier, 'predict_proba'):
                    probabilities = classifier.predict_proba(text_vector)[0]
                    confidence = float(max(probabilities))
                else:
                    confidence = 0.8  # Дефолтная уверенность
                
                classification[task_name] = prediction
                classification[f"{task_name}_confidence"] = confidence
            
            # Извлекаем сущности
            entities = extract_entities(text) if extract_entities else {}
            
            return {
                "type": classification.get("type", "Approval Request"),
                "confidence": classification.get("type_confidence", 0.7),
                "urgency": classification.get("urgency", "medium"),
                "urgency_confidence": classification.get("urgency_confidence", 0.7),
                "tone": classification.get("tone", "formal"),
                "tone_confidence": classification.get("tone_confidence", 0.7),
                "entities": entities
            }
            
        except Exception as e:
            error_msg = f"Ошибка при ML классификации: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e


# Глобальный экземпляр классификатора
_ml_classifier_instance = None


def get_ml_classifier() -> MLClassifier:
    """Получает глобальный экземпляр ML классификатора"""
    global _ml_classifier_instance
    if _ml_classifier_instance is None:
        _ml_classifier_instance = MLClassifier()
    return _ml_classifier_instance

