"""
Работа с системными и пользовательскими промптами для YandexGPT.

Содержит функции для загрузки системного промпта, выбора стиля по типу письма
и построения пользовательского промпта с контекстом.
"""

import json
from pathlib import Path
from typing import Optional, Dict

from .llm_client import YandexGPTGenerator, get_generator


def load_system_prompt(prompt_file: str | None = None) -> str:
    """
    Загружает системный промпт.

    Приоритет источников:
    1. Явно переданный файл prompt_file
    2. system_prompt.md в корне проекта
    """
    # 1) Если передали конкретный файл – пробуем его
    if prompt_file is not None:
        prompt_path = Path(prompt_file)
        if prompt_path.exists():
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read().strip()

    # 2) Пробуем system_prompt.md рядом с корнем проекта
    system_md = Path(__file__).parent.parent / "system_prompt.md"
    if system_md.exists():
        with open(system_md, "r", encoding="utf-8") as f:
            return f.read().strip()

    raise FileNotFoundError(
        "Не удалось найти системный промпт.\n"
        "Создайте файл system_prompt.md в корне проекта "
        "или укажите путь к промпту явно."
    )


def _get_style_guidance(classification: str) -> str:
    """
    Возвращает рекомендации по стилю для конкретного типа письма.
    """
    style_guides = {
        "Official Complaint or Claim": """
СТИЛЬ ДЛЯ ОФИЦИАЛЬНОЙ ЖАЛОБЫ/ПРЕТЕНЗИИ:
- Извиняющийся и понимающий тон
- Признание проблемы и ответственности банка
- Конкретные шаги по решению проблемы
- Указание сроков рассмотрения и ответа
- Предложение компенсации или исправления ситуации (если уместно)
- Контактные данные для дальнейшего общения""",
        "Regulatory Request": """
СТИЛЬ ДЛЯ РЕГУЛЯТОРНОГО ЗАПРОСА:
- Официальный, формальный стиль
- Ссылки на нормативные акты и регламенты
- Точные юридические формулировки
- Соблюдение требований регулятора
- Структурированное изложение информации
- Указание на соответствие требованиям""",
        "Partnership Proposal": """
СТИЛЬ ДЛЯ ПАРТНЕРСКОГО ПРЕДЛОЖЕНИЯ:
- Деловой, заинтересованный тон
- Профессиональная оценка предложения
- Указание на процедуры рассмотрения
- Предложение дальнейших шагов (встреча, переговоры)
- Благодарность за предложение
- Контактные данные ответственного лица""",
        "Information/Document Request": """
СТИЛЬ ДЛЯ ЗАПРОСА ИНФОРМАЦИИ/ДОКУМЕНТОВ:
- Четкий, структурированный ответ
- Указание конкретных документов и сроков предоставления
- Способы получения документов
- Требования к оформлению (если есть)
- Контактные данные для уточнений
- Благодарность за обращение""",
        "Notification or Information": """
СТИЛЬ ДЛЯ УВЕДОМЛЕНИЯ/ИНФОРМАЦИИ:
- Информативный, нейтральный стиль
- Четкое изложение фактов
- Структурированная подача информации
- Важные детали выделены
- Контактные данные для вопросов
- Профессиональный тон""",
        "Approval Request": """
СТИЛЬ ДЛЯ ЗАПРОСА НА ОДОБРЕНИЕ/СОГЛАСОВАНИЕ:
- Профессиональный деловой тон
- Четкость и конкретность в изложении
- Указание на важность и обоснованность запроса
- Готовность предоставить дополнительную информацию
- Указание сроков рассмотрения
- Вежливое обращение""",
    }

    return style_guides.get(
        classification,
        """
СТИЛЬ ДЛЯ ОБЩЕГО ПИСЬМА:
- Профессиональный деловой тон
- Четкость и конкретность
- Вежливое обращение
- Структурированное изложение
- Готовность к сотрудничеству""",
    )


def generate_reply(
    text: str,
    classification: str,
    fields: Dict,
    generator: Optional[YandexGPTGenerator] = None,
    prompt_file: Optional[str] = None,
    system_prompt_override: Optional[str] = None,
    temperature: float = 0.6,
    max_tokens: int = 2000,
) -> str:
    """
    Генерирует официальное деловое письмо банка высокого уровня.
    """
    if generator is None:
        generator = get_generator()

    # Загружаем системный промпт
    if system_prompt_override:
        system_prompt = system_prompt_override
    elif prompt_file:
        system_prompt = load_system_prompt(prompt_file)
    else:
        system_prompt = load_system_prompt()

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

    reply = generator.generate(
        prompt=user_prompt,
        system_prompt=system_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    return reply.strip()


__all__ = ["load_system_prompt", "generate_reply"]


