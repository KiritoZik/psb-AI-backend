# psb-AI-backend

Backend для работы с AI моделями через Yandex Cloud YandexGPT API.

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

## Использование

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
├── requirements.txt
├── example_usage.py
└── README.md
```