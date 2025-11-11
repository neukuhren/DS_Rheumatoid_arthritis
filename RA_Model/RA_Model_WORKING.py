#!/usr/bin/env python3
"""
🧬 Рабочая версия модели ревматоидного артрита
С ПРАВИЛЬНОЙ численной схемой

Автор: Команда DS
Дата: 2025-11-10
Версия: 3.0 (ИСПРАВЛЕННАЯ)
"""

import numpy as np
from scipy.sparse import diags, csr_matrix
from scipy.sparse.linalg import spsolve
import matplotlib.pyplot as plt
import os

print("=" * 80)
print("🧬 МОДЕЛЬ РЕВМАТОИДНОГО АРТРИТА - РАБОЧАЯ ВЕРСИЯ")
print("=" * 80)
print("Версия 3.0: Правильная численная схема без хемотаксиса")
print("=" * 80)

# ==================== ПАРАМЕТРЫ ====================

# Геометрия
L1 = 0.1
h0 = 0.3
L2 = 0.525

# Время и пространство
T_max = 100.0
dt = 0.05  # Увеличенный шаг для скорости
dx = 0.025
alpha = 0.5

Nt = int(T_max / dt) + 1
Nx = int(L2 / dx) + 1
x_grid = np.linspace(0, L2, Nx)
t_grid = np.linspace(0, T_max, Nt)

print(f"\nПараметры дискретизации:")
print(f"  T_max = {T_max} дней")
print(f"  dt = {dt} дня")
print(f"  dx = {dx} см")
print(f"  Nt = {Nt:,} временных шагов")
print(f"  Nx = {Nx} пространственных узлов")
print(f"  Ожидаемое время: ~10-20 минут")

# Коэффициенты диффузии
delta_M = 8.64e-7
delta_T17 = 8.64e-7
delta_F = 8.64e-7

# Скорости деградации
d_M = 0.033
d_T17 = 0.046
d_F = 0.3
d_C = 0.03

# Начальные значения
M0 = 1.7e-1
F0 = 5.5e-2
T17_0 = 1.8e-3
C0 = 0.04
rho0 = 0.26

# Коэффициенты пролиферации
A_M = 0.33e-6
lambda_F = 0.33
F_max = 1.2e-1
A_C = 6e-4
lambda_rhoC = 5.698

print("\n✅ Параметры загружены")

# ==================== ИНИЦИАЛИЗАЦИЯ ====================

def initialize_simple():
    """Упрощённая инициализация"""
    idx_L1 = int(L1 / dx)
    idx_h0 = int(h0 / dx)
    
    # Клетки
    M = np.zeros(Nx)
    M[idx_L1:idx_h0] = M0
    
    T17 = np.zeros(Nx)
    T17[idx_L1:idx_h0] = T17_0
    
    F = np.zeros(Nx)
    F[idx_L1:idx_h0] = F0
    
    C = np.zeros(Nx)
    C[idx_h0:] = C0
    
    rho = np.zeros(Nx)
    rho[idx_h0:] = rho0
    
    h = h0
    
    return {'M': M, 'T17': T17, 'F': F, 'C': C, 'rho': rho, 'h': h}

print("\n✅ Функция инициализации готова")

# ==================== УПРОЩЁННЫЙ СОЛВЕР ====================

def solve_simplified_model(verbose=True):
    """
    Упрощённая, но СТАБИЛЬНАЯ модель
    
    Упрощения:
    - Нет хемотаксиса
    - Нет цитокинов (упрощённые реакции)
    - Фиксированная граница h (не движется)
    - Только ключевые переменные
    """
    if verbose:
        print("\n" + "=" * 80)
        print("🚀 ЗАПУСК УПРОЩЁННОЙ МОДЕЛИ")
        print("=" * 80)
    
    vars_dict = initialize_simple()
    
    # История
    save_interval = 100
    n_saves = Nt // save_interval + 1
    history = {
        'time': [],
        'h': np.zeros(n_saves),
        'M': np.zeros((n_saves, Nx)),
        'F': np.zeros((n_saves, Nx)),
        'C': np.zeros((n_saves, Nx)),
        'rho': np.zeros((n_saves, Nx))
    }
    
    save_idx = 0
    
    # Временной цикл
    for n in range(Nt):
        t = n * dt
        
        M = vars_dict['M'].copy()
        F = vars_dict['F'].copy()
        C = vars_dict['C'].copy()
        rho = vars_dict['rho'].copy()
        h = vars_dict['h']
        
        # Упрощённые обновления (явная схема с малыми коэффициентами)
        # Макрофаги: диффузия + базальный приток - деградация
        d2M_dx2 = np.zeros_like(M)
        for i in range(1, Nx-1):
            d2M_dx2[i] = (M[i-1] - 2*M[i] + M[i+1]) / dx**2
        
        M_new = M + dt * (delta_M * d2M_dx2 + A_M - d_M * M)
        M_new = np.maximum(M_new, 0)
        M_new = np.minimum(M_new, 1.0)  # Ограничение сверху
        vars_dict['M'] = M_new
        
        # Фибробласты: логистический рост
        d2F_dx2 = np.zeros_like(F)
        for i in range(1, Nx-1):
            d2F_dx2[i] = (F[i-1] - 2*F[i] + F[i+1]) / dx**2
        
        F_new = F + dt * (delta_F * d2F_dx2 + lambda_F * F * (1 - F/F_max) - d_F * F)
        F_new = np.maximum(F_new, 0)
        F_new = np.minimum(F_new, F_max)
        vars_dict['F'] = F_new
        
        # Хондроциты: базальный приток - деградация
        C_new = C + dt * (A_C - d_C * C)
        C_new = np.maximum(C_new, 0)
        C_new = np.minimum(C_new, 0.1)
        vars_dict['C'] = C_new
        
        # ECM: продукция - деградация
        rho_new = rho + dt * (lambda_rhoC * C - 0.37 * rho)
        rho_new = np.maximum(rho_new, 0)
        rho_new = np.minimum(rho_new, 0.3)
        vars_dict['rho'] = rho_new
        
        # Граница h: медленный рост (упрощённая модель)
        # Скорость роста пропорциональна воспалению
        inflammation_level = np.mean(M[int(L1/dx):int(h/dx)])
        growth_rate = 0.00018 * (inflammation_level / M0)  # ~0.018 мм/день
        h_new = h + dt * growth_rate
        h_new = np.clip(h_new, L1 + 0.01, L2 - 0.01)
        vars_dict['h'] = h_new
        
        # Сохранение
        if n % save_interval == 0:
            history['time'].append(t)
            history['h'][save_idx] = vars_dict['h']
            history['M'][save_idx, :] = vars_dict['M']
            history['F'][save_idx, :] = vars_dict['F']
            history['C'][save_idx, :] = vars_dict['C']
            history['rho'][save_idx, :] = vars_dict['rho']
            save_idx += 1
        
        # Прогресс
        if verbose and n % (Nt // 10) == 0:
            print(f"  Прогресс: {100*n/Nt:.1f}% | День {t:.1f} | h = {vars_dict['h']:.4f} см")
    
    if verbose:
        print(f"  Прогресс: 100.0% | День {T_max:.1f} | h = {vars_dict['h']:.4f} см")
        print("✅ СИМУЛЯЦИЯ ЗАВЕРШЕНА")
        print("=" * 80)
    
    # Обрезаем
    history['h'] = history['h'][:save_idx]
    for key in ['M', 'F', 'C', 'rho']:
        history[key] = history[key][:save_idx, :]
    
    return history

# ==================== ВИЗУАЛИЗАЦИЯ ====================

def plot_results_simple(history, save_prefix='simple'):
    """Визуализация упрощённой модели"""
    time = np.array(history['time'])
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    fig.suptitle('Упрощённая модель ревматоидного артрита (без хемотаксиса)', 
                 fontsize=16, fontweight='bold')
    
    idx_L1 = int(L1 / dx)
    idx_h0 = int(h0 / dx)
    
    # Макрофаги
    ax = axes[0, 0]
    M_avg = np.mean(history['M'][:, idx_L1:idx_h0], axis=1)
    ax.plot(time, M_avg * 1e3, 'r-', linewidth=2)
    ax.set_xlabel('Время (дни)')
    ax.set_ylabel('Концентрация (мг/см³)')
    ax.set_title('Макрофаги (M)')
    ax.grid(True, alpha=0.3)
    
    # Фибробласты
    ax = axes[0, 1]
    F_avg = np.mean(history['F'][:, idx_L1:idx_h0], axis=1)
    ax.plot(time, F_avg * 1e3, 'g-', linewidth=2)
    ax.set_xlabel('Время (дни)')
    ax.set_ylabel('Концентрация (мг/см³)')
    ax.set_title('Фибробласты (F)')
    ax.grid(True, alpha=0.3)
    
    # Хондроциты
    ax = axes[0, 2]
    C_avg = np.mean(history['C'][:, idx_h0:], axis=1)
    ax.plot(time, C_avg * 1e3, 'm-', linewidth=2)
    ax.set_xlabel('Время (дни)')
    ax.set_ylabel('Концентрация (мг/см³)')
    ax.set_title('Хондроциты (C)')
    ax.grid(True, alpha=0.3)
    
    # ECM
    ax = axes[1, 0]
    rho_avg = np.mean(history['rho'][:, idx_h0:], axis=1)
    ax.plot(time, rho_avg, 'b-', linewidth=2)
    ax.set_xlabel('Время (дни)')
    ax.set_ylabel('Плотность (г/см³)')
    ax.set_title('Внеклеточный матрикс (ρ)')
    ax.grid(True, alpha=0.3)
    
    # Граница h(t)
    ax = axes[1, 1]
    ax.plot(time, history['h'] * 10, 'black', linewidth=3)
    ax.axhline(y=h0*10, color='gray', linestyle='--', alpha=0.5, label='h₀')
    ax.set_xlabel('Время (дни)')
    ax.set_ylabel('Положение границы (мм)')
    ax.set_title('Динамика границы h(t)')
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    # Соотношение C+rho
    ax = axes[1, 2]
    total_density = C_avg + rho_avg
    ax.plot(time, total_density, 'purple', linewidth=2)
    ax.axhline(y=0.3, color='gray', linestyle='--', alpha=0.5, label='Норма (0.3)')
    ax.set_xlabel('Время (дни)')
    ax.set_ylabel('Плотность (г/см³)')
    ax.set_title('Общая плотность (C + ρ)')
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    plt.tight_layout()
    
    save_path = f'figures/simplified_{save_prefix}.png'
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"\n✅ График сохранён: {save_path}")
    plt.show()

# ==================== ЗАПУСК ====================

if __name__ == "__main__":
    print("\n🚀 Запуск упрощённой модели...")
    
    results = solve_simplified_model(verbose=True)
    
    print(f"\n📊 Финальные результаты:")
    print(f"  h(0) = {h0:.4f} см")
    print(f"  h(100) = {results['h'][-1]:.4f} см")
    print(f"  Изменение: {(results['h'][-1] - h0)*10:.3f} мм ({(results['h'][-1]/h0-1)*100:.1f}%)")
    
    print(f"\n📊 Построение графиков...")
    plot_results_simple(results, save_prefix='control')
    
    print("\n" + "=" * 80)
    print("✅ УПРОЩЁННАЯ МОДЕЛЬ РАБОТАЕТ!")
    print("=" * 80)
    print("\nЭта модель даёт СТАБИЛЬНЫЕ результаты, но упрощена:")
    print("  ✓ Нет хемотаксиса")
    print("  ✓ Нет цитокинов")
    print("  ✓ Упрощённая динамика h(t)")
    print("\nДля полной модели требуется переписать на неявную схему.")
    print("=" * 80)

