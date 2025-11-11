#!/usr/bin/env python3
"""
🚀 Скрипт для запуска симуляции модели ревматоидного артрита

Использование:
    python run_simulation.py

Результаты будут сохранены в папке results/
"""

import sys
import os
import time
from datetime import datetime

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 70)
print("🧬 ЗАПУСК СИМУЛЯЦИИ МОДЕЛИ РЕВМАТОИДНОГО АРТРИТА")
print("=" * 70)
print(f"📅 Дата и время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"📂 Рабочая директория: {os.getcwd()}")
print("=" * 70)
print()

# Импортируем необходимые модули
print("📦 Загрузка модулей...")
try:
    import numpy as np
    from scipy.sparse import diags
    from scipy.sparse.linalg import spsolve
    import matplotlib
    matplotlib.use('Agg')  # Для работы без GUI
    import matplotlib.pyplot as plt
    import pandas as pd
    print("✅ Все модули успешно загружены!")
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("   Установите необходимые пакеты: pip install numpy scipy matplotlib pandas")
    sys.exit(1)

print()
print("=" * 70)
print("📝 ПРИМЕЧАНИЕ:")
print("=" * 70)
print("Для полного запуска симуляции рекомендуется использовать Jupyter Notebook.")
print("Откройте RA_Model.ipynb в Jupyter и запустите все ячейки.")
print()
print("Команды для запуска:")
print("  1. jupyter notebook RA_Model.ipynb")
print("  2. В меню выберите: Cell -> Run All")
print()
print("Или в терминале:")
print("  jupyter nbconvert --execute RA_Model.ipynb --to notebook \\")
print("    --ExecutePreprocessor.timeout=7200 \\")
print("    --ExecutePreprocessor.kernel_name=python3 \\")
print("    --output RA_Model_executed.ipynb")
print("=" * 70)
print()

# Создаем папки для результатов если их нет
os.makedirs('results', exist_ok=True)
os.makedirs('figures/temporal_dynamics', exist_ok=True)
os.makedirs('figures/spatial_profiles', exist_ok=True)
os.makedirs('figures/treatment_comparison', exist_ok=True)

print("✅ Папки для результатов готовы")
print()

# Создаем лог-файл с инструкциями
log_file = 'results/simulation_info.txt'
with open(log_file, 'w', encoding='utf-8') as f:
    f.write("=" * 70 + "\n")
    f.write("ИНФОРМАЦИЯ О СИМУЛЯЦИИ МОДЕЛИ РЕВМАТОИДНОГО АРТРИТА\n")
    f.write("=" * 70 + "\n")
    f.write(f"Дата создания: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write("\n")
    f.write("ИНСТРУКЦИИ ПО ЗАПУСКУ:\n")
    f.write("-" * 70 + "\n")
    f.write("1. Откройте RA_Model.ipynb в Jupyter Notebook\n")
    f.write("2. Запустите все ячейки: Cell -> Run All\n")
    f.write("3. Дождитесь завершения (~2-3 часа)\n")
    f.write("\n")
    f.write("ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ:\n")
    f.write("-" * 70 + "\n")
    f.write("- Контрольная симуляция (без лечения)\n")
    f.write("- Инфликсимаб (анти-TNF-α)\n")
    f.write("- Метотрексат (иммуносупрессор)\n")
    f.write("- Тоцилизумаб (анти-IL-6)\n")
    f.write("\n")
    f.write("ГРАФИКИ:\n")
    f.write("-" * 70 + "\n")
    f.write("- figures/temporal_dynamics/ - временная динамика\n")
    f.write("- figures/spatial_profiles/ - пространственные профили\n")
    f.write("- figures/treatment_comparison/ - сравнение терапий\n")
    f.write("\n")
    f.write("=" * 70 + "\n")

print(f"📄 Информация сохранена в: {log_file}")
print()

print("=" * 70)
print("🎯 ГОТОВО К ЗАПУСКУ!")
print("=" * 70)
print("📓 Откройте RA_Model.ipynb в Jupyter Notebook для запуска симуляции")
print("=" * 70)

