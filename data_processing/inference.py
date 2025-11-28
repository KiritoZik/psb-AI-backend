# inference.py
import joblib
import sys
import os
from preprocessing import enhanced_preprocess_text, extract_entities

# Папка с моделями
MODELS_DIR = 'models'
INPUT_FILE = 'input.txt'
OUTPUT_FILE = 'output.txt'

def load_hyperparameters(filename='parameters.txt'):
    """Загружает гиперпараметры из файла."""
    hyperparams = {}
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            key, value = line.strip().split(': ')
            # Преобразуем типы данных
            if key == 'max_features':
                value = int(value)
            elif key == 'ngram_range':
                value = tuple(map(int, value.strip('()').split(', ')))
            elif key == 'min_df':
                value = int(value)
            elif key == 'max_df':
                value = float(value)
            elif key == 'C':
                value = float(value)
            elif key == 'max_iter':
                value = int(value)
            hyperparams[key] = value
    return hyperparams

def load_models():
    """Загружает обученные модели из папки models."""
    tasks = ['type', 'urgency', 'tone']
    models = {}
    
    for task_name in tasks:
        try:
            vectorizer_path = os.path.join(MODELS_DIR, f'vectorizer_{task_name}.pkl')
            classifier_path = os.path.join(MODELS_DIR, f'classifier_{task_name}.pkl')
            
            vectorizer = joblib.load(vectorizer_path)
            classifier = joblib.load(classifier_path)
            
            models[task_name] = {
                'vectorizer': vectorizer,
                'classifier': classifier
            }
        except FileNotFoundError:
            print(f"Модель для {task_name} не найдена в папке {MODELS_DIR}!")
            return None
    
    return models

def classify_email(text, models):
    """Классифицирует письмо и извлекает сущности."""
    # Извлекаем сущности
    entities = extract_entities(text)
    
    # Классифицируем по задачам
    classification = {}
    
    for task_name, model_data in models.items():
        # Предобработка текста
        processed_text = enhanced_preprocess_text(text, remove_personal_data_flag=True)
        
        # Векторизация
        vectorizer = model_data['vectorizer']
        text_vector = vectorizer.transform([processed_text])
        
        # Классификация
        classifier = model_data['classifier']
        prediction = classifier.predict(text_vector)[0]
        
        classification[task_name] = prediction
    
    return {
        'type': classification['type'],
        'urgency': classification['urgency'],
        'tone': classification['tone'],
        'entities': entities
    }

def save_to_file(result, filename=OUTPUT_FILE):
    """Сохраняет результат в файл в требуемом формате."""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"{result['type']}\n")
        f.write(f"{result['urgency']}\n")
        f.write(f"{result['tone']}\n")
        f.write(f"{result['entities']}\n")

def read_input_text(filename=INPUT_FILE):
    """Читает текст письма из файла."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            text = f.read().strip()
        return text
    except FileNotFoundError:
        print(f"Файл {filename} не найден!")
        return None
    except Exception as e:
        print(f"Ошибка при чтении файла {filename}: {e}")
        return None

def main():
    """Основная функция для классификации."""
    # Проверяем существование папки с моделями
    if not os.path.exists(MODELS_DIR):
        print(f"Ошибка: папка с моделями '{MODELS_DIR}' не найдена!")
        print("Сначала выполните обучение: python training.py")
        return
    
    # Загружаем гиперпараметры и модели
    hyperparams = load_hyperparameters()
    models = load_models()
    
    if models is None:
        print("Ошибка загрузки моделей!")
        return
    
    # Получаем текст письма
    email_text = None
    
    # Пытаемся прочитать из файла input.txt
    email_text = read_input_text()
    
    # Если файла нет, пробуем другие способы
    if email_text is None:
        if len(sys.argv) > 1:
            # Если текст передан как аргумент командной строки
            email_text = ' '.join(sys.argv[1:])
        else:
            # Если аргументов нет, запрашиваем ввод
            email_text = input("Введите текст письма: ").strip()
    
    if not email_text:
        print("Ошибка: текст письма не может быть пустым!")
        return
    
    # Классифицируем письмо
    result = classify_email(email_text, models)
    
    # Выводим результат в консоль в подробном формате
    print(f"Тип письма: {result['type']}")
    print(f"Срочность: {result['urgency']}")
    print(f"Тон: {result['tone']}")
    print(f"Сущности: {result['entities']}")
    
    # Сохраняем результат в файл в компактном формате
    save_to_file(result)
    

if __name__ == "__main__":
    main()