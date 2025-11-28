# preprocessing.py
import re
import string
from typing import List, Dict, Any

try:
    import pymorphy3
    morph = pymorphy3.MorphAnalyzer()
    USE_LEMMATIZATION = True
except ImportError:
    USE_LEMMATIZATION = False

# Русские стоп-слова
RUSSIAN_STOP_WORDS = {
    'и', 'в', 'во', 'не', 'что', 'он', 'на', 'я', 'с', 'со', 'как', 'а', 'то', 'все',
    'она', 'так', 'его', 'но', 'да', 'ты', 'к', 'у', 'же', 'вы', 'за', 'бы', 'по',
    'только', 'ее', 'мне', 'было', 'вот', 'от', 'меня', 'еще', 'нет', 'о', 'из',
    'ему', 'теперь', 'когда', 'даже', 'ну', 'вдруг', 'ли', 'если', 'уже', 'или',
    'ни', 'быть', 'был', 'него', 'до', 'вас', 'нибудь', 'опять', 'уж', 'вам', 'ведь',
    'там', 'потом', 'себя', 'ничего', 'ей', 'может', 'они', 'тут', 'где', 'есть'
}

def remove_punctuation(text: str) -> str:
    """Удаляет пунктуацию из текста."""
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def remove_numbers(text: str) -> str:
    """Удаляет числа из текста."""
    text = re.sub(r'\d+', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def tokenize(text: str) -> List[str]:
    """Разбивает текст на токены (слова)."""
    tokens = text.lower().split()
    return tokens

def remove_stop_words(tokens: List[str], stop_words: set = None) -> List[str]:
    """Удаляет стоп-слова из списка токенов."""
    if stop_words is None:
        stop_words = RUSSIAN_STOP_WORDS
    return [token for token in tokens if token not in stop_words]

def lemmatize_tokens(tokens: List[str]) -> List[str]:
    """Выполняет лемматизацию токенов."""
    if not USE_LEMMATIZATION:
        return tokens
    
    lemmatized = []
    for token in tokens:
        parsed = morph.parse(token)[0]
        lemmatized.append(parsed.normal_form)
    return lemmatized

def extract_entities(text: str) -> Dict[str, List[str]]:
    """Извлекает персональные данные и другие сущности из текста."""
    result = {
        'names': [],
        'dates': [],
        'contract_numbers': [],
        'account_numbers': []
    }

    # Паттерны для ФИО
    full_name_pattern = r'\b[А-ЯЁ][а-яё]{2,}(?:ов|ев|ин|ын|ая|ья|ий|ой)?\s+[А-ЯЁ][а-яё]{2,}\s+[А-ЯЁ][а-яё]{2,}(?:ич|вна|вич|овна|евич|ельевна)?'
    full_names = re.findall(full_name_pattern, text)
    
    for name in full_names:
        exclude_words = ['уважаемый', 'просим', 'требуем', 'сообщаем', 'информируем', 'подтверждаем']
        first_word = name.split()[0].lower()
        if first_word not in exclude_words and name not in result['names']:
            result['names'].append(name)

    initials_pattern = r'\b[А-ЯЁ][а-яё]{2,}(?:ов|ев|ин|ын|ая|ья|ий|ой)?\s+[А-ЯЁ]\.\s*[А-ЯЁ]\.'
    initials_matches = re.findall(initials_pattern, text)
    for match in initials_matches:
        if match not in result['names']:
            result['names'].append(match)

    # Паттерны для дат
    date_patterns = [
        r'\d{1,2}-\d{1,2}\s+[а-яё]+\s+\d{4}\s+года?',
        r'\d{1,2}\s+[а-яё]+\s+\d{4}\s+года?',
        r'\d{1,2}\.\d{1,2}\.\d{4}',
        r'\d{4}-\d{1,2}-\d{1,2}',
    ]
    
    found_dates = set()
    for pattern in date_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            is_subset = any(match in d or d in match for d in found_dates if match != d)
            if not is_subset:
                found_dates.add(match)
                result['dates'].append(match)

    # Паттерны для номеров договоров
    contract_patterns = [
        r'№+[А-ЯЁ]{1,3}-?\d{1,6}',
        r'договор[ауе]?\s+№+[А-ЯЁ]{0,3}-?\d{1,6}',
    ]
    
    for pattern in contract_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            clean_match = re.sub(r'договор[ауе]?\s+', '', match, flags=re.IGNORECASE).strip()
            if clean_match not in result['contract_numbers']:
                result['contract_numbers'].append(clean_match)

    # Паттерны для номеров счетов
    account_patterns = [
        r'счет[ауе]?\s+№?\s*\d{5,}',
        r'№\s*\d{16,}',
        r'\b\d{16,}\b',
    ]
    
    for pattern in account_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            numbers = re.findall(r'\d{5,}', match)
            for number in numbers:
                if len(number) >= 16 and number not in result['account_numbers']:
                    result['account_numbers'].append(number)

    return result

def remove_personal_data(text: str) -> str:
    """Удаляет персональные данные из текста, заменяя их на метки."""
    processed_text = text
    entities = extract_entities(text)
    
    for name in entities['names']:
        processed_text = processed_text.replace(name, '[ФИО]')
    for date in entities['dates']:
        processed_text = processed_text.replace(date, '[ДАТА]')
    for contract in entities['contract_numbers']:
        processed_text = processed_text.replace(contract, '[НОМЕР_ДОГОВОРА]')
    for account in entities['account_numbers']:
        processed_text = processed_text.replace(account, '[НОМЕР_СЧЕТА]')
    
    return processed_text

def enhanced_preprocess_text(text: str,
                           remove_personal_data_flag: bool = True,
                           remove_stop_words_flag: bool = True,
                           remove_punctuation_flag: bool = True,
                           remove_numbers_flag: bool = True,
                           lemmatize_flag: bool = True,
                           custom_stop_words: set = None) -> str:
    """Улучшенная функция предобработки с удалением персональных данных."""
    if not isinstance(text, str):
        text = str(text)

    if remove_personal_data_flag:
        text = remove_personal_data(text)

    text = text.lower()

    if remove_punctuation_flag:
        text = remove_punctuation(text)

    if remove_numbers_flag:
        text = remove_numbers(text)

    tokens = tokenize(text)

    if remove_stop_words_flag:
        tokens = remove_stop_words(tokens, custom_stop_words)

    if lemmatize_flag and USE_LEMMATIZATION:
        tokens = lemmatize_tokens(tokens)

    return ' '.join(tokens)