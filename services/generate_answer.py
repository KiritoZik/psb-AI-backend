"""
Сервис генерации ответов через Yandex Cloud LLM
Обращается к YandexGPT API для генерации деловых писем
Использует системный промпт и шаблоны по типам писем
"""

from pathlib import Path
from typing import Dict, Optional
from generator import YandexGPTGenerator, get_generator, generate_reply


# Маппинг типов ML на имена файлов шаблонов
CLASSIFICATION_TO_TEMPLATE = {
    "Official Complaint or Claim": "complaint",
    "Regulatory Request": "regulatory",
    "Partnership Proposal": "partner_offer",
    "Information/Document Request": "document_request",
    "Notification or Information": "notification",
    "Approval Request": "notification"  # Используем notification как общий шаблон
}


def load_template(classification: str) -> Optional[str]:
    """
    Загружает шаблон для конкретного типа письма
    
    :param classification: Тип письма (из ML модели)
    :return: Содержимое шаблона или None
    """
    # Маппим тип ML на имя файла шаблона
    template_name = CLASSIFICATION_TO_TEMPLATE.get(classification, classification.lower().replace(" ", "_").replace("/", "_"))
    
    template_file = f"ai/prompts/templates/{template_name}.md"
    template_path = Path(template_file)
    
    # Пробуем разные пути
    if not template_path.exists():
        template_path = Path(__file__).parent.parent / "ai" / "prompts" / "templates" / f"{template_name}.md"
    
    if not template_path.exists():
        # Если шаблон не найден, возвращаем None
        return None
    
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return None


def load_system_prompt() -> str:
    """
    Загружает системный промпт (использует общий helper из generator.prompts)
    
    :return: Содержимое системного промпта
    """
    from generator.prompts import load_system_prompt as load_default
    return load_default()


def generate_answer(
    text: str,
    classification: str,
    fields: Optional[Dict] = None,
    generator: Optional[YandexGPTGenerator] = None
) -> str:
    """
    Генерирует ответ на письмо через Yandex Cloud LLM
    
    Использует:
    - system_prompt.md - системный промпт
    - ai/prompts/templates/{classification}.md - шаблон для типа письма
    
    :param text: Текст входящего письма
    :param classification: Тип письма (Official Complaint or Claim, Regulatory Request, Partnership Proposal, Information/Document Request, Notification or Information, Approval Request)
    :param fields: Извлеченные поля из письма (даты, номера договоров, суммы и т.д.)
    :param generator: Экземпляр генератора (если None, создается новый)
    :return: Сгенерированный ответ
    """
    if fields is None:
        fields = {}
    
    # Загружаем системный промпт из system_prompt.md
    system_prompt = load_system_prompt()
    
    # Загружаем шаблон для данного типа письма (если есть)
    template = load_template(classification)
    
    # Если есть шаблон, добавляем его к системному промпту
    if template:
        system_prompt = f"{system_prompt}\n\n## Шаблон для типа письма '{classification}':\n\n{template}"
    
    # Используем generate_reply с кастомным системным промптом
    return generate_reply(
        text=text,
        classification=classification,
        fields=fields,
        generator=generator,
        system_prompt_override=system_prompt
    )


__all__ = ["generate_answer", "load_template", "load_system_prompt"]

