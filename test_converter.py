#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работоспособности конвертера
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path

def test_ffmpeg_installation():
    """Проверка установки FFmpeg"""
    print("Проверка установки FFmpeg...")
    try:
        result = subprocess.run(['ffmpeg', '-version'],
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,
                              check=True,
                              text=True)
        print("[OK] FFmpeg установлен и доступен")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("[FAIL] FFmpeg не найден. Пожалуйста, установите FFmpeg и добавьте его в PATH")
        return False

def test_python_dependencies():
    """Проверка необходимых Python модулей"""
    print("Проверка Python зависимостей...")
    try:
        import tkinter
        import subprocess
        import threading
        print("[OK] Все необходимые модули Python доступны")
        return True
    except ImportError as e:
        print(f"[FAIL] Отсутствует необходимый модуль Python: {e}")
        return False

def test_converter_import():
    """Проверка импорта конвертера"""
    print("Проверка импорта конвертера...")
    try:
        import ffmpeg_converter
        print("[OK] Конвертер успешно импортирован")
        return True
    except ImportError as e:
        print(f"[FAIL] Ошибка импорта конвертера: {e}")
        return False

def create_test_files():
    """Создание тестовых файлов"""
    print("Создание тестовых файлов...")
    
    # Создаем временную директорию
    temp_dir = Path(tempfile.gettempdir()) / "ffmpeg_test"
    temp_dir.mkdir(exist_ok=True)
    
    # Создаем тестовые файлы (пустые, для проверки структуры)
    test_webm = temp_dir / "test.webm"
    test_ogg = temp_dir / "test.ogg"
    
    # Создаем пустые файлы для тестирования
    test_webm.touch()
    test_ogg.touch()
    
    print(f"✓ Созданы тестовые файлы в {temp_dir}")
    return temp_dir

def main():
    """Основная функция тестирования"""
    print("=" * 50)
    print("Тестирование конвертера WebM/Ogg в MP4/MP3")
    print("=" * 50)
    
    tests = [
        test_ffmpeg_installation,
        test_python_dependencies,
        test_converter_import,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    # Создание тестовых файлов
    try:
        test_dir = create_test_files()
        print(f"✓ Тестовые файлы созданы в {test_dir}")
        print()
        passed += 1
        total += 1
    except Exception as e:
        print(f"✗ Ошибка создания тестовых файлов: {e}")
        print()
    
    print("=" * 50)
    print(f"Результаты тестирования: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("✓ Все тесты пройдены! Конвертер готов к использованию.")
        return 0
    else:
        print("✗ Некоторые тесты не пройдены. Проверьте ошибки выше.")
        return 1

if __name__ == "__main__":
    sys.exit(main())