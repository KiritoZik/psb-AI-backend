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


def generate_reply(
    text: str,
    classification: str,
    fields: Dict,
    generator: Optional[YandexGPTGenerator] = None,
    prompt_file: str = "generator/prompt.txt",
    temperature: float = 0.7,
    max_tokens: int = 2000
) -> str:
    """
    Генерирует официальный корпоративный ответ на email
    
    :param text: Текст входящего email
    :param classification: Тип email (complaint, regulatory, partner_offer, document_request, notification)
    :param fields: Извлеченные поля (даты, номера договоров, суммы, ключевые фразы)
    :param generator: Экземпляр YandexGPTGenerator (если None, создается новый)
    :param prompt_file: Путь к файлу с системным промптом
    :param temperature: Температура генерации
    :param max_tokens: Максимальное количество токенов
    :return: Сгенерированный официальный ответ
    """
    if generator is None:
        generator = get_generator()
    
    # Загружаем системный промпт
    system_prompt = load_system_prompt(prompt_file)
    
    # Формируем промпт с контекстом
    fields_str = json.dumps(fields, ensure_ascii=False, indent=2) if fields else "Не найдено"
    
    user_prompt = f"""Тип письма: {classification}

Извлеченные поля:
{fields_str}

Текст входящего письма:
{text}

Сгенерируй официальный корпоративный ответ на это письмо."""
    
    # Генерируем ответ
    reply = generator.generate(
        prompt=user_prompt,
        system_prompt=system_prompt,
        temperature=temperature,
        max_tokens=max_tokens
    )
    
    return reply.strip()

