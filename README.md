# psb-AI-backend

Backend для работы с AI моделями через Yandex Cloud YandexGPT API.

## Возможности

- ✅ Подключение к YandexGPT API
- ✅ Генерация текста через LLM
- ✅ FastAPI backend с REST API
- ✅ Обработка писем и генерация ответов

## Установка

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Создайте файл `.env` в корне проекта со следующими переменными:
```
YANDEX_API_KEY=your_api_key_here
YANDEX_FOLDER_ID=your_folder_id_here
YANDEX_MODEL_URI=gpt://yandexgpt/latest  # опционально
```

## Получение учетных данных

1. **API ключ**: 
   - Зайдите в [консоль Yandex Cloud](https://console.cloud.yandex.ru/)
   - Перейдите в раздел "Сервисные аккаунты" или "API ключи"
   - Создайте новый API ключ

2. **Folder ID**:
   - В консоли Yandex Cloud откройте нужный каталог
   - Folder ID можно найти в URL или в настройках каталога

## Запуск API сервера

1. Запустите FastAPI сервер:
```bash
python app.py
```

Или с помощью uvicorn:
```bash
uvicorn app:app --reload
```

2. API будет доступен по адресу: `http://localhost:8000`

3. Документация API доступна по адресу: `http://localhost:8000/docs`

## API Endpoints

### POST /api/reply
Обрабатывает входящее письмо и генерирует ответ через LLM.

**Запрос:**
```json
{
  "text": "Текст входящего письма",
  "system_prompt": "Опциональный системный промпт",
  "temperature": 0.7,
  "max_tokens": 2000
}
```

**Ответ:**
```json
{
  "success": true,
  "reply": "Сгенерированный ответ от LLM"
}
```

**Пример использования:**
```bash
curl -X POST "http://localhost:8000/api/reply" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Здравствуйте! Прошу предоставить информацию о ваших услугах.",
    "temperature": 0.7,
    "max_tokens": 500
  }'
```

### GET /health
Проверка состояния сервиса.

### GET /
Информация о API и доступных endpoints.

## Использование (Python библиотека)

### Простой пример

```python
from generator import YandexGPTGenerator

# Создаем генератор (настройки берутся из .env)
generator = YandexGPTGenerator()

# Генерируем текст
response = generator.generate(
    prompt="Расскажи о Python",
    temperature=0.7,
    max_tokens=500
)

print(response)
```

### С системным промптом

```python
from generator import YandexGPTGenerator

generator = YandexGPTGenerator()

response = generator.generate(
    prompt="Напиши краткое резюме",
    system_prompt="Ты опытный редактор",
    temperature=0.6,
    max_tokens=300
)
```

### Потоковая генерация

```python
from generator import YandexGPTGenerator

generator = YandexGPTGenerator()

for chunk in generator.generate_stream(
    prompt="Расскажи о машинном обучении",
    max_tokens=500
):
    print(chunk, end="", flush=True)
```

### Использование PromptBuilder

```python
from generator import YandexGPTGenerator, PromptBuilder

builder = PromptBuilder(
    system_prompt="Ты полезный AI-ассистент"
)
builder.add_user_message("Что такое Python?")

generator = YandexGPTGenerator()
response = generator.generate(
    prompt=builder.get_user_prompt(),
    system_prompt=builder.get_system_prompt()
)
```

Более подробные примеры см. в файле `example_usage.py`.

## Структура проекта

```
psb-AI-backend/
├── generator/
│   ├── __init__.py
│   ├── generator.py    # Класс YandexGPTGenerator
│   └── prompt.py       # Класс PromptBuilder
├── app.py              # FastAPI приложение
├── requirements.txt
├── example_usage.py
├── test_api.py         # Тесты API endpoints
├── test_connection.py  # Тест подключения к YandexGPT
└── README.md
```

## Тестирование API

### Через Python скрипт

Запустите тестовый скрипт для проверки API:
```bash
python test_api.py
```

Убедитесь, что сервер запущен перед тестированием.

### Через Postman

1. **Импортируйте готовую коллекцию:**
   - Откройте Postman
   - Нажмите `Import`
   - Выберите файл `Email_Reply_API.postman_collection.json`
   - Коллекция будет импортирована со всеми готовыми запросами

2. **Или создайте запросы вручную:**
   - См. подробную инструкцию в файле `POSTMAN_GUIDE.md`

3. **Настройте переменную:**
   - В коллекции установите переменную `base_url = http://localhost:8000`
   - Или измените URL в каждом запросе вручную