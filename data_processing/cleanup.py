# cleanup.py
import os
import shutil
import glob

def cleanup_files():
    """Очищает все временные файлы и папки"""
    
    # Папка с моделями
    models_dir = 'models'
    
    # Удаляем всю папку с моделями
    if os.path.exists(models_dir):
        shutil.rmtree(models_dir)
        print(f"Удалена папка {models_dir}")
    
    # Удаляем отдельные файлы
    files_to_remove = [
        'parameters.txt',
        'output.txt',
        'result.txt'
    ]
    
    for file_pattern in files_to_remove:
        for file_path in glob.glob(file_pattern):
            try:
                os.remove(file_path)
                print(f"Удален файл: {file_path}")
            except FileNotFoundError:
                pass
    
    # Очищаем кэш Python
    pycache_dirs = glob.glob('**/__pycache__', recursive=True)
    for dir_path in pycache_dirs:
        shutil.rmtree(dir_path)
        print(f"Удалена папка: {dir_path}")
    
    # Удаляем .pyc файлы
    pyc_files = glob.glob('**/*.pyc', recursive=True)
    for file_path in pyc_files:
        try:
            os.remove(file_path)
            print(f"Удален файл: {file_path}")
        except FileNotFoundError:
            pass
    
    print("Очистка завершена!")

if __name__ == "__main__":
    cleanup_files()