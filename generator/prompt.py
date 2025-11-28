from typing import Optional, Dict, List


class PromptBuilder:
    """Класс для построения и управления промптами"""
    
    def __init__(self, system_prompt: Optional[str] = None):
        """
        Инициализация построителя промптов
        
        Args:
            system_prompt: Базовый системный промпт
        """
        self.system_prompt = system_prompt
        self.messages: List[Dict[str, str]] = []
        
        if system_prompt:
            self.messages.append({
                "role": "system",
                "text": system_prompt
            })
    
    def add_user_message(self, text: str) -> "PromptBuilder":
        """
        Добавить сообщение пользователя
        
        Args:
            text: Текст сообщения
        
        Returns:
            self для цепочки вызовов
        """
        self.messages.append({
            "role": "user",
            "text": text
        })
        return self
    
    def add_assistant_message(self, text: str) -> "PromptBuilder":
        """
        Добавить сообщение ассистента (для контекста диалога)
        
        Args:
            text: Текст сообщения
        
        Returns:
            self для цепочки вызовов
        """
        self.messages.append({
            "role": "assistant",
            "text": text
        })
        return self
    
    def set_system_prompt(self, text: str) -> "PromptBuilder":
        """
        Установить системный промпт
        
        Args:
            text: Текст системного промпта
        
        Returns:
            self для цепочки вызовов
        """
        self.system_prompt = text
        # Обновляем системное сообщение, если оно уже есть
        if self.messages and self.messages[0]["role"] == "system":
            self.messages[0]["text"] = text
        else:
            self.messages.insert(0, {"role": "system", "text": text})
        return self
    
    def get_messages(self) -> List[Dict[str, str]]:
        """
        Получить список сообщений
        
        Returns:
            Список сообщений в формате для API
        """
        return self.messages.copy()
    
    def get_user_prompt(self) -> str:
        """
        Получить последнее сообщение пользователя
        
        Returns:
            Текст последнего пользовательского сообщения
        """
        for message in reversed(self.messages):
            if message["role"] == "user":
                return message["text"]
        return ""
    
    def get_system_prompt(self) -> Optional[str]:
        """
        Получить системный промпт
        
        Returns:
            Текст системного промпта или None
        """
        return self.system_prompt
    
    def clear(self) -> "PromptBuilder":
        """
        Очистить все сообщения (кроме системного промпта)
        
        Returns:
            self для цепочки вызовов
        """
        if self.system_prompt:
            self.messages = [{"role": "system", "text": self.system_prompt}]
        else:
            self.messages = []
        return self
    
    def build_simple_prompt(self, user_text: str) -> str:
        """
        Построить простой промпт из пользовательского текста
        
        Args:
            user_text: Текст пользователя
        
        Returns:
            Готовый промпт для генерации
        """
        if self.system_prompt:
            return f"{self.system_prompt}\n\n{user_text}"
        return user_text

