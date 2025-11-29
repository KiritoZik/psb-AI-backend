"""
Извлекатель полей из текста письма
Извлекает даты, номера договоров, суммы, ключевые фразы
Интегрирован с data_processing/preprocessing.py для улучшенного извлечения
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# Пытаемся использовать улучшенное извлечение из data_processing
ML_EXTRACTION_AVAILABLE = False
ml_extract_entities = None

try:
    data_processing_path = Path(__file__).parent.parent / "data_processing"
    if data_processing_path.exists():
        sys.path.insert(0, str(data_processing_path.parent))
        from data_processing.preprocessing import extract_entities as ml_extract_entities
        ML_EXTRACTION_AVAILABLE = True
except ImportError:
    # ML извлечение недоступно, используем только базовое
    ML_EXTRACTION_AVAILABLE = False
    ml_extract_entities = None


class FieldExtractor:
    """Извлекает структурированные данные из текста письма"""
    
    def __init__(self):
        # Паттерны для извлечения данных
        self.date_patterns = [
            r'\d{1,2}[./-]\d{1,2}[./-]\d{2,4}',  # ДД.ММ.ГГГГ или ДД/ММ/ГГГГ
            r'\d{4}[./-]\d{1,2}[./-]\d{1,2}',  # ГГГГ.ММ.ДД
            r'\d{1,2}\s+(январ|феврал|март|апрел|май|июн|июл|август|сентябр|октябр|ноябр|декабр)[а-я]*\s+\d{4}',
            r'\d{1,2}\s+(янв|фев|мар|апр|май|июн|июл|авг|сен|окт|ноя|дек)[а-я.]*\s+\d{4}',
        ]
        
        self.contract_patterns = [
            r'(?:договор|контракт|соглашение|дог\.?)\s*[№#]?\s*[А-Яа-я]?[-]?\d+',
            r'[№#]\s*\d+[-/]\d+',  # Номер вида №123-45
            r'[А-Я]{1,3}[-]?\d+',  # Буквенно-цифровой номер (Д-12345)
        ]
        
        self.amount_patterns = [
            r'\d{1,3}(?:\s?\d{3})*(?:[.,]\d{2})?\s*(?:руб|рублей|руб\.|₽|RUB)',
            r'\d{1,3}(?:\s?\d{3})*(?:[.,]\d{2})?\s*(?:usd|доллар|долл\.|\$)',
            r'\d{1,3}(?:\s?\d{3})*(?:[.,]\d{2})?\s*(?:eur|евро|€)',
            r'\d{1,3}(?:\s?\d{3})*(?:[.,]\d{2})?',  # Просто число (может быть суммой)
        ]
        
        # Ключевые фразы для извлечения
        self.key_phrases_patterns = [
            r'(?:срок|дата|до|который день)\s+\d{1,2}[./-]\d{1,2}[./-]\d{2,4}',
            r'(?:сумма|размер|объем|количество)\s+\d+',
            r'(?:номер|№|#)\s*\d+',
        ]
    
    def extract_dates(self, text: str) -> List[str]:
        """
        Извлекает даты из текста
        
        :param text: Текст письма
        :return: Список найденных дат
        """
        dates = []
        
        for pattern in self.date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            dates.extend(matches)
        
        # Удаляем дубликаты и сортируем
        unique_dates = list(set(dates))
        return unique_dates
    
    def extract_contract_numbers(self, text: str) -> List[str]:
        """
        Извлекает номера договоров, контрактов, соглашений
        
        :param text: Текст письма
        :return: Список найденных номеров
        """
        contract_numbers = []
        
        for pattern in self.contract_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            contract_numbers.extend(matches)
        
        # Очищаем и нормализуем
        cleaned = []
        for num in contract_numbers:
            # Убираем лишние пробелы
            cleaned_num = re.sub(r'\s+', ' ', num.strip())
            if cleaned_num not in cleaned:
                cleaned.append(cleaned_num)
        
        return cleaned
    
    def extract_amounts(self, text: str) -> List[str]:
        """
        Извлекает суммы денег из текста
        
        :param text: Текст письма
        :return: Список найденных сумм
        """
        amounts = []
        
        for pattern in self.amount_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            amounts.extend(matches)
        
        # Удаляем дубликаты
        unique_amounts = list(set(amounts))
        return unique_amounts
    
    def extract_key_phrases(self, text: str, max_phrases: int = 10) -> List[str]:
        """
        Извлекает ключевые фразы из текста
        
        :param text: Текст письма
        :param max_phrases: Максимальное количество фраз
        :return: Список ключевых фраз
        """
        phrases = []
        
        # Извлекаем фразы с важными словами
        important_words = [
            "срочно", "важно", "необходимо", "требуется", "прошу",
            "жалоба", "претензия", "требование", "запрос", "обращение"
        ]
        
        sentences = re.split(r'[.!?]\s+', text)
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            for word in important_words:
                if word in sentence_lower and len(sentence.strip()) > 10:
                    phrases.append(sentence.strip())
                    break
        
        # Ограничиваем количество
        return phrases[:max_phrases]
    
    def extract_sender_name(self, text: str) -> Optional[str]:
        """
        Пытается извлечь имя отправителя из текста письма
        
        :param text: Текст письма
        :return: Имя отправителя или None
        """
        # Паттерны для поиска имени в начале письма
        patterns = [
            r'(?:с\s+уважением|уважаем|здравствуйте|добрый\s+(?:день|вечер|утро)),?\s+([А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+)',
            r'^([А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+)',
            r'(?:подпис|от\s+лица|инициатор):\s*([А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                name = match.group(1).strip()
                # Проверяем, что это похоже на имя (не слишком длинное)
                if len(name.split()) <= 3 and len(name) < 50:
                    return name
        
        return None
    
    def extract_email(self, text: str) -> Optional[str]:
        """
        Извлекает email адрес из текста
        
        :param text: Текст письма
        :return: Email адрес или None
        """
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(email_pattern, text)
        return match.group(0) if match else None
    
    def extract_phone(self, text: str) -> Optional[str]:
        """
        Извлекает номер телефона из текста
        
        :param text: Текст письма
        :return: Номер телефона или None
        """
        phone_patterns = [
            r'\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}',
            r'\+7\s?\(?\d{3}\)?\s?\d{3}[-.\s]?\d{2}[-.\s]?\d{2}',
        ]
        
        for pattern in phone_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0).strip()
        
        return None
    
    def extract_all(self, text: str) -> Dict:
        """
        Извлекает все поля из текста письма
        
        Использует ТОЛЬКО ML извлечение из data_processing. Базовое извлечение используется
        только как дополнение к ML результатам.
        
        :param text: Текст письма
        :return: Словарь с извлеченными полями
        :raises RuntimeError: Если ML извлечение недоступно
        """
        if not ML_EXTRACTION_AVAILABLE or ml_extract_entities is None:
            error_msg = (
                "ML извлечение сущностей недоступно. Убедитесь, что:\n"
                f"1. Модуль data_processing/preprocessing.py существует\n"
                f"2. Функция extract_entities доступна\n"
                f"3. Установлены зависимости: pip install pymorphy3"
            )
            import logging
            logger = logging.getLogger(__name__)
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        base_result = {
            "dates": self.extract_dates(text),
            "contract_numbers": self.extract_contract_numbers(text),
            "amounts": self.extract_amounts(text),
            "key_phrases": self.extract_key_phrases(text),
            "sender_name": self.extract_sender_name(text),
            "email": self.extract_email(text),
            "phone": self.extract_phone(text)
        }
        
        try:
            ml_entities = ml_extract_entities(text)
            
            result = {
                "dates": list(set(base_result["dates"] + ml_entities.get("dates", []))),
                "contract_numbers": list(set(base_result["contract_numbers"] + ml_entities.get("contract_numbers", []))),
                "amounts": base_result["amounts"],
                "key_phrases": base_result["key_phrases"],
                "sender_name": ml_entities.get("names", [None])[0] if ml_entities.get("names") else base_result["sender_name"],
                "email": base_result["email"],
                "phone": base_result["phone"]
            }
            
            if ml_entities.get("account_numbers"):
                result["account_numbers"] = ml_entities["account_numbers"]
            
            return result
            
        except Exception as e:
            error_msg = f"Ошибка при ML извлечении сущностей: {e}"
            import logging
            logger = logging.getLogger(__name__)
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

