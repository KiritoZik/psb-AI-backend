import os
import json
import requests
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
        """Создает список сообщений для API"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "text": system_prompt})
        messages.append({"role": "user", "text": prompt})
        return messages
    
    def _create_payload(self, messages: List[Dict[str, str]], temperature: float, 
                       max_tokens: int, stream: bool = False) -> Dict:
        """Создает payload для запроса"""
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
        """Формирует сообщение об ошибке"""
        try:
            error_detail = error.response.json()
        except:
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

