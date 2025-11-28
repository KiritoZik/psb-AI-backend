# training.py
import pandas as pd
import joblib
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score

# Импортируем функции предобработки из preprocessing.py
from preprocessing import enhanced_preprocess_text

# Создаем папку для моделей
MODELS_DIR = 'models'
os.makedirs(MODELS_DIR, exist_ok=True)

def load_data(csv_path: str = 'data.csv'):
    """Загружает данные из CSV файла."""
    df = pd.read_csv(csv_path)
    texts = df['text'].values
    types = df['type'].values
    urgencies = df['urgency'].values
    tones = df['tone'].values
    return texts, types, urgencies, tones

def split_data(X, y, test_size=0.15, val_size=0.15, random_state=42):
    """Разделяет данные на обучающую, валидационную и тестовую выборки."""
    X_temp, X_test, y_temp, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )
    
    val_size_adjusted = val_size / (1 - test_size)
    X_train, X_val, y_train, y_val = train_test_split(
        X_temp, y_temp, test_size=val_size_adjusted, random_state=random_state, stratify=y_temp
    )
    
    return X_train, X_val, X_test, y_train, y_val, y_test

def train_task_model(texts, labels, task_name, hyperparams):
    """Обучает модель для конкретной задачи."""
    # Разделение данных
    X_train, X_val, X_test, y_train, y_val, y_test = split_data(texts, labels)
    
    # Предобработка и векторизация
    processed_texts = [
        enhanced_preprocess_text(text, remove_personal_data_flag=True)
        for text in X_train
    ]
    
    vectorizer = TfidfVectorizer(
        max_features=hyperparams['max_features'],
        ngram_range=hyperparams['ngram_range'],
        min_df=hyperparams['min_df'],
        max_df=hyperparams['max_df']
    )
    X_train_vectors = vectorizer.fit_transform(processed_texts)
    
    # Обучение модели
    classifier = LogisticRegression(
        C=hyperparams['C'],
        max_iter=hyperparams['max_iter'],
        random_state=42
    )
    classifier.fit(X_train_vectors, y_train)
    
    return vectorizer, classifier

def save_hyperparameters(hyperparams, filename='parameters.txt'):
    """Сохраняет гиперпараметры в файл."""
    with open(filename, 'w', encoding='utf-8') as f:
        for key, value in hyperparams.items():
            f.write(f"{key}: {value}\n")

def main():
    """Основная функция обучения."""
    # Гиперпараметры
    hyperparams = {
        'max_features': 10000,
        'ngram_range': (1, 2),
        'min_df': 1,
        'max_df': 0.95,
        'C': 1.0,
        'max_iter': 1000
    }
    
    # Сохраняем гиперпараметры
    save_hyperparameters(hyperparams)
    
    # Загружаем данные
    texts, types, urgencies, tones = load_data('data.csv')
    
    # Обучаем модели для каждой задачи
    tasks = {
        'type': types,
        'urgency': urgencies, 
        'tone': tones
    }
    
    models = {}
    
    for task_name, labels in tasks.items():
        print(f"Обучение модели для {task_name}...")
        vectorizer, classifier = train_task_model(texts, labels, task_name, hyperparams)
        
        models[task_name] = {
            'vectorizer': vectorizer,
            'classifier': classifier
        }
        
        # Сохраняем модели в папку models
        joblib.dump(vectorizer, os.path.join(MODELS_DIR, f'vectorizer_{task_name}.pkl'))
        joblib.dump(classifier, os.path.join(MODELS_DIR, f'classifier_{task_name}.pkl'))
    
    print("Обучение завершено! Модели сохранены в папку 'models'")

if __name__ == "__main__":
    main()