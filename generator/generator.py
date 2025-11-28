import os
import json
import requests
from pathlib import Path
from typing import Optional, Dict, List
from dotenv import load_dotenv

load_dotenv()


class YandexGPTGenerator:
    """Класс для работы с YandexGPT API"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        folder_id: Optional[str] = None,
        model_uri: Optional[str] = None
    ):
        """
        Инициализация подключения к YandexGPT
        
        Args:
            api_key: API ключ (или из YANDEX_API_KEY)
            folder_id: ID каталога (или из YANDEX_FOLDER_ID)
            model_uri: URI модели (по умолчанию yandexgpt/latest)
        """
        self.api_key = api_key or os.getenv("YANDEX_API_KEY")
        self.folder_id = folder_id or os.getenv("YANDEX_FOLDER_ID")
        model_name = model_uri or os.getenv("YANDEX_MODEL_URI", "yandexgpt/latest")
        
        if not self.api_key:
            raise ValueError("API ключ не указан. Установите YANDEX_API_KEY или передайте api_key")
        
        if not self.folder_id:
            raise ValueError("Folder ID не указан. Установите YANDEX_FOLDER_ID или передайте folder_id")
        
        # Формируем modelUri: gpt://folder_id/model_name
        if model_name.startswith("gpt://"):
            # Если уже полный URI, используем как есть
            self.model_uri = model_name
        else:
            # Добавляем folder_id к имени модели
            self.model_uri = f"gpt://{self.folder_id}/{model_name}"
        
        self.base_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        self.headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def _create_messages(self, prompt: str, system_prompt: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Создает список сообщений для API
        :param prompt: Промпт пользователя
        :param system_prompt: Системный промпт (опционально)
        :return: Список сообщений в формате API
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "text": system_prompt})
        messages.append({"role": "user", "text": prompt})
        return messages

    def _create_payload(self, messages: List[Dict[str, str]], temperature: float,
                       max_tokens: int, stream: bool = False) -> Dict:
        """
        Создает payload для запроса к API
        :param messages: Список сообщений
        :param temperature: Температура генерации
        :param max_tokens: Максимальное количество токенов
        :param stream: Включить потоковую генерацию
        :return: Словарь с payload для запроса
        """
        return {
            "modelUri": self.model_uri,
            "completionOptions": {
                "stream": stream,
                "temperature": temperature,
                "maxTokens": max_tokens
            },
            "messages": messages
        }

    def _get_error_message(self, error: requests.exceptions.HTTPError, payload: Dict) -> str:
        """
        Формирует сообщение об ошибке с деталями
        :param error: Исключение HTTPError
        :param payload: Payload запроса для отладки
        :return: Строка с детальным описанием ошибки
        """
        try:
            error_detail = error.response.json()
        except Exception:
            error_detail = error.response.text[:200]

        return (f"Ошибка YandexGPT API: {error}\n"
                f"Детали: {error_detail}\n"
                f"Запрос: {json.dumps(payload, ensure_ascii=False, indent=2)}")

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.6,
        max_tokens: int = 2000
    ) -> str:
        """
        Генерация текста
        Args:
            prompt: Промпт для генерации
            system_prompt: Системный промпт (опционально)
            temperature: Температура (0.0-1.0)
            max_tokens: Максимум токенов
        
        Returns:
            Сгенерированный текст
        """
        messages = self._create_messages(prompt, system_prompt)
        payload = self._create_payload(messages, temperature, max_tokens, stream=False)
        
        try:
            response = requests.post(self.base_url, headers=self.headers, json=payload)
            response.raise_for_status()
            result = response.json()
            return result["result"]["alternatives"][0]["message"]["text"]
        except requests.exceptions.HTTPError as e:
            raise Exception(self._get_error_message(e, payload))
        except requests.exceptions.RequestException as e:
            raise Exception(f"Ошибка подключения: {e}")
    
    def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.6,
        max_tokens: int = 2000
    ):
        """
        Потоковая генерация текста
        Args:
            prompt: Промпт для генерации
            system_prompt: Системный промпт (опционально)
            temperature: Температура (0.0-1.0)
            max_tokens: Максимум токенов
        
        Yields:
            Части сгенерированного текста
        """
        messages = self._create_messages(prompt, system_prompt)
        payload = self._create_payload(messages, temperature, max_tokens, stream=True)
        
        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                stream=True
            )
            response.raise_for_status()
            
            for line in response.iter_lines():
                if not line:
                    continue
                
                line_str = line.decode('utf-8')
                if not line_str.startswith('data: '):
                    continue
                
                data_str = line_str[6:]
                if data_str == '[DONE]':
                    break
                
                try:
                    data = json.loads(data_str)
                    if "result" in data and "alternatives" in data["result"]:
                        text = data["result"]["alternatives"][0].get("message", {}).get("text", "")
                        if text:
                            yield text
                except json.JSONDecodeError:
                    continue
        
        except requests.exceptions.HTTPError as e:
            raise Exception(self._get_error_message(e, payload))
        except requests.exceptions.RequestException as e:
            raise Exception(f"Ошибка подключения: {e}")


def get_generator() -> YandexGPTGenerator:
    """Создает генератор с настройками из .env"""
    return YandexGPTGenerator()


def load_system_prompt(prompt_file: str = "generator/prompt.txt") -> str:
    """
    Загружает системный промпт из файла
    
    :param prompt_file: Путь к файлу с промптом
    :return: Содержимое файла с промптом
    """
    prompt_path = Path(prompt_file)
    
    # Пробуем разные пути
    if not prompt_path.exists():
        # Пробуем относительно корня проекта
        prompt_path = Path(__file__).parent.parent / "generator" / "prompt.txt"
    
    if not prompt_path.exists():
        # Пробуем в той же директории что и generator.py
        prompt_path = Path(__file__).parent / "prompt.txt"
    
    if not prompt_path.exists():
        raise FileNotFoundError(
            f"Файл с промптом не найден: {prompt_file}\n"
            f"Проверьте наличие файла generator/prompt.txt"
        )
    
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read().strip()


def _get_style_guidance(classification: str) -> str:
    """
    Возвращает рекомендации по стилю для конкретного типа письма
    
    :param classification: Тип письма
    :return: Текст с рекомендациями по стилю
    """
    style_guides = {
        "complaint": """
СТИЛЬ ДЛЯ ЖАЛОБЫ:
- Извиняющийся и понимающий тон
- Признание проблемы и ответственности банка
- Конкретные шаги по решению проблемы
- Указание сроков рассмотрения и ответа
- Предложение компенсации или исправления ситуации (если уместно)
- Контактные данные для дальнейшего общения""",
        
        "regulatory": """
СТИЛЬ ДЛЯ РЕГУЛЯТОРНОГО ЗАПРОСА:
- Официальный, формальный стиль
- Ссылки на нормативные акты и регламенты
- Точные юридические формулировки
- Соблюдение требований регулятора
- Структурированное изложение информации
- Указание на соответствие требованиям""",
        
        "partner_offer": """
СТИЛЬ ДЛЯ ПАРТНЕРСКОГО ПРЕДЛОЖЕНИЯ:
- Деловой, заинтересованный тон
- Профессиональная оценка предложения
- Указание на процедуры рассмотрения
- Предложение дальнейших шагов (встреча, переговоры)
- Благодарность за предложение
- Контактные данные ответственного лица""",
        
        "document_request": """
СТИЛЬ ДЛЯ ЗАПРОСА ДОКУМЕНТОВ:
- Четкий, структурированный ответ
- Указание конкретных документов и сроков предоставления
- Способы получения документов
- Требования к оформлению (если есть)
- Контактные данные для уточнений
- Благодарность за обращение""",
        
        "notification": """
СТИЛЬ ДЛЯ УВЕДОМЛЕНИЯ:
- Информативный, нейтральный стиль
- Четкое изложение фактов
- Структурированная подача информации
- Важные детали выделены
- Контактные данные для вопросов
- Профессиональный тон"""
    }
    
    return style_guides.get(classification.lower(), """
СТИЛЬ ДЛЯ ОБЩЕГО ПИСЬМА:
- Профессиональный деловой тон
- Четкость и конкретность
- Вежливое обращение
- Структурированное изложение
- Готовность к сотрудничеству""")


def generate_reply(
    text: str,
    classification: str,
    fields: Dict,
    generator: Optional[YandexGPTGenerator] = None,
    prompt_file: str = "generator/prompt.txt",
    temperature: float = 0.6,
    max_tokens: int = 2000
) -> str:
    """
    Генерирует официальное деловое письмо банка высокого уровня
    
    Функция обеспечивает:
    - Генерацию делового письма официального уровня
    - Адаптацию стиля под тип письма
    - Исключение юридических ошибок
    - Соблюдение корпоративного стиля банка
    
    :param text: Текст входящего письма
    :param classification: Тип письма (complaint, regulatory, partner_offer, document_request, notification)
    :param fields: Извлеченные поля (даты, номера договоров, суммы, ключевые фразы)
    :param generator: Экземпляр YandexGPTGenerator (если None, создается новый)
    :param prompt_file: Путь к файлу с системным промптом
    :param temperature: Температура генерации (рекомендуется 0.6 для более точных ответов)
    :param max_tokens: Максимальное количество токенов
    :return: Сгенерированное официальное деловое письмо
    """
    if generator is None:
        generator = get_generator()
    
    # Загружаем системный промпт
    system_prompt = load_system_prompt(prompt_file)
    
    # Получаем рекомендации по стилю для данного типа письма
    style_guidance = _get_style_guidance(classification)
    
    # Формируем промпт с контекстом
    fields_str = json.dumps(fields, ensure_ascii=False, indent=2) if fields else "Не найдено"
    
    user_prompt = f"""ТИП ПИСЬМА: {classification.upper()}

{style_guidance}

ИЗВЛЕЧЕННЫЕ ПОЛЯ ИЗ ВХОДЯЩЕГО ПИСЬМА:
{fields_str}

ТЕКСТ ВХОДЯЩЕГО ПИСЬМА:
{text}

ЗАДАЧА:
Сгенерируй официальное деловое письмо банка, которое:
1. Соответствует официальному уровню деловой переписки
2. Адаптировано под тип письма ({classification})
3. Исключает юридические ошибки
4. Соблюдает корпоративный стиль банка
5. Использует извлеченные поля точно как указано
6. Имеет правильную структуру делового письма

ВАЖНО:
- Не выдумывай информацию, которой нет во входящем письме
- Используй только указанные даты, номера договоров, суммы
- Соблюдай профессиональный тон банка
- Избегай юридических формулировок, которые могут создать риски"""
    
    # Генерируем ответ с более низкой температурой для точности
    reply = generator.generate(
        prompt=user_prompt,
        system_prompt=system_prompt,
        temperature=temperature,
        max_tokens=max_tokens
    )
    
    return reply.strip()
