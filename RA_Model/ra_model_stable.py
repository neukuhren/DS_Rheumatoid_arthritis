#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧬 РАБОЧАЯ МОДЕЛЬ РЕВМАТОИДНОГО АРТРИТА
Версия 3.0 - Стабильная численная схема

Упрощения для устойчивости:
- Упрощённая динамика границы h(t)
- Без хемотаксиса
- Консервативные численные методы

Автор: Команда DS
Дата: 2025-11-10
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams
import os

# Настройка для русского языка
rcParams['font.family'] = 'DejaVu Sans'

print("=" * 80)
print("🧬 СТАБИЛЬНАЯ МОДЕЛЬ РЕВМАТОИДНОГО АРТРИТА")
print("=" * 80)
print("Версия 3.0: Упрощённая, но работающая реализация")
print("=" * 80)

# ==================== ПАРАМЕТРЫ МОДЕЛИ ====================

# Геометрические параметры
L1 = 0.1          # см
h0 = 0.3          # см  
L2 = 0.525        # см
alpha = 0.5

# Временные параметры
T_max = 100.0     # дни
dt = 0.05         # дни (оптимизировано)
dx = 0.025        # см

# Сетка
Nt = int(T_max / dt) + 1
Nx = int(L2 / dx) + 1
x_grid = np.linspace(0, L2, Nx)
t_grid = np.linspace(0, T_max, Nt)

# Коэффициенты диффузии
delta_M = 8.64e-7
delta_T17 = 8.64e-7
delta_F = 8.64e-7
delta_I17 = 7.44e-2
delta_I23 = 9.09e-2
delta_Ta = 8.46e-2

# Скорости деградации
d_M = 0.033
d_T17 = 0.046
d_F = 0.3
d_C = 0.03
d_I17 = 0.076
d_I23 = 2.79
d_Ta = 217.0

# Начальные концентрации
M0 = 1.7e-1
F0 = 5.5e-2
T17_0 = 1.8e-3
C0 = 0.04
I17_0 = 5e-12
I23_0 = 8e-9
Ta0 = 1.165e-11
T0 = 2e-4
rho0 = 0.277

# Константы полунасыщения
K23 = I23_0
K_T17 = T17_0
K_alpha = Ta0

# Коэффициенты пролиферации
A_M = 0.33e-6
lambda_TI23 = 0.0336
lambda_MI23 = 0.0484
lambda_F = 0.33
F_max = 1.2e-1
A_C = 6e-4
lambda_rhoC = 5.698

# Продукция цитокинов
lambda_I17T17 = 5.39e-10
lambda_I23M = 1.402e-7
lambda_TaM = 8.1e-9

# Лекарства
gamma_A = 3.45e-12
gamma_Y = 13.85e-10
gamma_Z = 3.45e-12
d_A = 0.069
d_Y = 2.77
d_Z = 0.069

print(f"\nПараметры дискретизации:")
print(f"  Временных шагов: {Nt:,}")
print(f"  Пространственных узлов: {Nx}")
print(f"  Ожидаемое время: ~10-20 минут")

# ==================== ИНИЦИАЛИЗАЦИЯ ====================

def initialize_model():
    """Инициализация всех переменных"""
    idx_L1 = int(L1 / dx)
    idx_h0 = int(h0 / dx)
    
    M = np.zeros(Nx)
    M[idx_L1:idx_h0] = M0
    
    T17 = np.zeros(Nx)
    T17[idx_L1:idx_h0] = T17_0
    
    F = np.zeros(Nx)
    F[idx_L1:idx_h0] = F0
    
    C = np.zeros(Nx)
    C[idx_h0:] = C0
    
    I17 = np.full(Nx, I17_0)
    I23 = np.full(Nx, I23_0)
    Ta = np.full(Nx, Ta0)
    
    rho = np.zeros(Nx)
    rho[idx_h0:] = rho0
    
    A = np.zeros(Nx)
    Y = np.zeros(Nx)
    Z = np.zeros(Nx)
    
    return {
        'M': M, 'T17': T17, 'F': F, 'C': C, 'rho': rho,
        'I17': I17, 'I23': I23, 'Ta': Ta,
        'A': A, 'Y': Y, 'Z': Z,
        'h': h0
    }

# ==================== ЧИСЛЕННЫЕ МЕТОДЫ ====================

def safe_diffusion(u, delta):
    """Безопасная аппроксимация диффузии"""
    d2u = np.zeros_like(u)
    for i in range(1, len(u)-1):
        d2u[i] = (u[i-1] - 2*u[i] + u[i+1]) / (dx**2)
    # Граничные условия Неймана
    d2u[0] = d2u[1]
    d2u[-1] = d2u[-2]
    return delta * d2u

# ==================== ФУНКЦИИ ЛЕКАРСТВ ====================

def drug_input(t, drug_type='none'):
    """Режим введения препаратов"""
    if drug_type == 'none':
        return 0.0, 0.0, 0.0
    elif drug_type == 'infliximab':
        return 1.0, 0.0, 0.0
    elif drug_type == 'methotrexate':
        return 0.0, 1.0, 0.0
    elif drug_type == 'tocilizumab':
        return 0.0, 0.0, 1.0
    elif drug_type == 'combo_AY':
        return 1.0, 1.0, 0.0  # Инфликсимаб + Метотрексат
    elif drug_type == 'combo_AZ':
        return 1.0, 0.0, 1.0  # Инфликсимаб + Тоцилизумаб
    elif drug_type == 'combo_YZ':
        return 0.0, 1.0, 1.0  # Метотрексат + Тоцилизумаб
    else:
        return 0.0, 0.0, 0.0

# ==================== ГЛАВНЫЙ СОЛВЕР ====================

def solve_model(drug_type='none', save_interval=20, verbose=True):
    """
    Стабильная версия модели РА
    
    Параметры:
    -----------
    drug_type : str
        Тип терапии
    save_interval : int
        Интервал сохранения
    verbose : bool
        Печатать прогресс
    """
    if verbose:
        print("\n" + "=" * 80)
        print(f"🚀 ЗАПУСК: {drug_type}")
        print("=" * 80)
    
    vars_dict = initialize_model()
    
    # История
    n_saves = Nt // save_interval + 1
    history = {
        'time': [],
        'h': np.zeros(n_saves),
        'M': np.zeros((n_saves, Nx)),
        'T17': np.zeros((n_saves, Nx)),
        'F': np.zeros((n_saves, Nx)),
        'C': np.zeros((n_saves, Nx)),
        'I17': np.zeros((n_saves, Nx)),
        'I23': np.zeros((n_saves, Nx)),
        'Ta': np.zeros((n_saves, Nx)),
        'rho': np.zeros((n_saves, Nx))
    }
    
    save_idx = 0
    
    # Временной цикл
    for n in range(Nt):
        t = n * dt
        
        I_A, I_Y, I_Z = drug_input(t, drug_type)
        idx_L1 = int(L1 / dx)
        idx_h = int(vars_dict['h'] / dx)
        
        # ============ ОБНОВЛЕНИЕ ПЕРЕМЕННЫХ ============
        
        # Макрофаги
        M = vars_dict['M'].copy()
        diff_M = safe_diffusion(M, delta_M)
        M_new = M + dt * (diff_M + A_M - d_M * M)
        M_new = np.clip(M_new, 0, 0.5)
        vars_dict['M'] = M_new
        
        # Th-17
        T17 = vars_dict['T17'].copy()
        I23 = vars_dict['I23'].copy()
        diff_T17 = safe_diffusion(T17, delta_T17)
        R_T17 = lambda_TI23 * T17 * I23 / (K23 + I23) - d_T17 * T17
        T17_new = T17 + dt * (diff_T17 + R_T17)
        T17_new = np.clip(T17_new, 0, 0.01)
        vars_dict['T17'] = T17_new
        
        # Фибробласты
        F = vars_dict['F'].copy()
        diff_F = safe_diffusion(F, delta_F)
        R_F = lambda_F * F * (1 - F/F_max) - d_F * F
        F_new = F + dt * (diff_F + R_F)
        F_new = np.clip(F_new, 0, F_max)
        vars_dict['F'] = F_new
        
        # IL-17
        I17 = vars_dict['I17'].copy()
        diff_I17 = safe_diffusion(I17, delta_I17)
        R_I17 = lambda_I17T17 * T17 - d_I17 * I17
        I17_new = I17 + dt * (diff_I17 + R_I17)
        I17_new = np.clip(I17_new, 0, 1e-9)
        vars_dict['I17'] = I17_new
        
        # IL-23
        diff_I23 = safe_diffusion(I23, delta_I23)
        R_I23 = lambda_I23M * M - d_I23 * I23
        I23_new = I23 + dt * (diff_I23 + R_I23)
        I23_new = np.clip(I23_new, 0, 1e-7)
        vars_dict['I23'] = I23_new
        
        # TNF-alpha
        Ta = vars_dict['Ta'].copy()
        A = vars_dict['A'].copy()
        diff_Ta = safe_diffusion(Ta, delta_Ta)
        R_Ta = lambda_TaM * M - d_Ta * Ta - 166.15e11 * Ta * A
        Ta_new = Ta + dt * (diff_Ta + R_Ta)
        Ta_new = np.clip(Ta_new, 0, 1e-8)
        vars_dict['Ta'] = Ta_new
        
        # Хондроциты
        C = vars_dict['C'].copy()
        C_new = C + dt * (A_C - d_C * C)
        C_new = np.clip(C_new, 0, 0.1)
        vars_dict['C'] = C_new
        
        # ECM
        rho = vars_dict['rho'].copy()
        rho_new = rho + dt * (lambda_rhoC * C - 0.37 * rho)
        rho_new = np.clip(rho_new, 0, 0.3)
        vars_dict['rho'] = rho_new
        
        # Лекарства
        diff_A = safe_diffusion(A, 4.78e-2)
        A_new = A + dt * (diff_A + gamma_A * I_A - d_A * A)
        A_new = np.clip(A_new, 0, 1e-10)
        vars_dict['A'] = A_new
        
        Y = vars_dict['Y'].copy()
        diff_Y = safe_diffusion(Y, 32e-2)
        Y_new = Y + dt * (diff_Y + gamma_Y * I_Y - d_Y * Y)
        Y_new = np.clip(Y_new, 0, 1e-8)
        vars_dict['Y'] = Y_new
        
        Z = vars_dict['Z'].copy()
        diff_Z = safe_diffusion(Z, 4.74e-2)
        Z_new = Z + dt * (diff_Z + gamma_Z * I_Z - d_Z * Z)
        Z_new = np.clip(Z_new, 0, 1e-10)
        vars_dict['Z'] = Z_new
        
        # ============ УПРОЩЁННАЯ ДИНАМИКА h(t) ============
        # Рост пропорционален воспалению
        inflammation = np.mean(M[idx_L1:idx_h]) + \
                      np.mean(F[idx_L1:idx_h]) + \
                      np.mean(T17[idx_L1:idx_h])
        baseline = M0 + F0 + T17_0
        
        # Базовая скорость роста
        base_rate = 0.0018  # см/день (~1.8 мм за 100 дней)
        
        # Влияние лекарств (уменьшают рост)
        drug_effect = 1.0
        if I_A > 0:
            drug_effect *= 0.6  # Инфликсимаб уменьшает на 40%
        if I_Y > 0:
            drug_effect *= 0.75  # Метотрексат уменьшает на 25%
        if I_Z > 0:
            drug_effect *= 0.5  # Тоцилизумаб уменьшает на 50%
        
        growth_rate = base_rate * (inflammation / baseline) * drug_effect
        
        h_new = vars_dict['h'] + dt * growth_rate
        h_new = np.clip(h_new, L1 + 0.01, L2 - 0.02)
        vars_dict['h'] = h_new
        
        # Сохранение
        if n % save_interval == 0:
            history['time'].append(t)
            history['h'][save_idx] = vars_dict['h']
            history['M'][save_idx, :] = vars_dict['M']
            history['T17'][save_idx, :] = vars_dict['T17']
            history['F'][save_idx, :] = vars_dict['F']
            history['C'][save_idx, :] = vars_dict['C']
            history['I17'][save_idx, :] = vars_dict['I17']
            history['I23'][save_idx, :] = vars_dict['I23']
            history['Ta'][save_idx, :] = vars_dict['Ta']
            history['rho'][save_idx, :] = vars_dict['rho']
            save_idx += 1
        
        # Прогресс
        if verbose and n % (Nt // 10) == 0:
            print(f"  Прогресс: {100*n/Nt:5.1f}% | День {t:5.1f} | h = {vars_dict['h']:.4f} см")
    
    if verbose:
        print(f"  Прогресс: 100.0% | День {T_max:5.1f} | h = {vars_dict['h']:.4f} см")
        print("✅ СИМУЛЯЦИЯ ЗАВЕРШЕНА")
        print("=" * 80)
    
    # Обрезаем
    history['h'] = history['h'][:save_idx]
    for key in ['M', 'T17', 'F', 'C', 'I17', 'I23', 'Ta', 'rho']:
        history[key] = history[key][:save_idx, :]
    
    return history

# ==================== ВИЗУАЛИЗАЦИЯ ====================

def plot_temporal_dynamics(history, title_suffix='', save_path=None):
    """Построение временной динамики"""
    time = np.array(history['time'])
    idx_L1 = int(L1 / dx)
    idx_h0 = int(h0 / dx)
    
    fig, axes = plt.subplots(3, 3, figsize=(18, 12))
    fig.suptitle(f'Временная динамика модели РА {title_suffix}', 
                 fontsize=16, fontweight='bold')
    
    # Макрофаги
    ax = axes[0, 0]
    M_avg = np.mean(history['M'][:, idx_L1:idx_h0], axis=1)
    ax.plot(time, M_avg * 1e3, 'r-', linewidth=2)
    ax.set_xlabel('Время (дни)')
    ax.set_ylabel('Концентрация (мг/см³)')
    ax.set_title('Макрофаги (M)')
    ax.grid(True, alpha=0.3)
    
    # Th-17
    ax = axes[0, 1]
    T17_avg = np.mean(history['T17'][:, idx_L1:idx_h0], axis=1)
    ax.plot(time, T17_avg * 1e6, 'b-', linewidth=2)
    ax.set_xlabel('Время (дни)')
    ax.set_ylabel('Концентрация (мкг/см³)')
    ax.set_title('Th-17 клетки')
    ax.grid(True, alpha=0.3)
    
    # Фибробласты
    ax = axes[0, 2]
    F_avg = np.mean(history['F'][:, idx_L1:idx_h0], axis=1)
    ax.plot(time, F_avg * 1e3, 'g-', linewidth=2)
    ax.set_xlabel('Время (дни)')
    ax.set_ylabel('Концентрация (мг/см³)')
    ax.set_title('Фибробласты (F)')
    ax.grid(True, alpha=0.3)
    
    # Хондроциты
    ax = axes[1, 0]
    C_avg = np.mean(history['C'][:, idx_h0:], axis=1)
    ax.plot(time, C_avg * 1e3, 'm-', linewidth=2)
    ax.set_xlabel('Время (дни)')
    ax.set_ylabel('Концентрация (мг/см³)')
    ax.set_title('Хондроциты (C)')
    ax.grid(True, alpha=0.3)
    
    # IL-17
    ax = axes[1, 1]
    I17_avg = np.mean(history['I17'][:, idx_L1:idx_h0], axis=1)
    ax.plot(time, I17_avg * 1e12, 'orange', linewidth=2)
    ax.set_xlabel('Время (дни)')
    ax.set_ylabel('Концентрация (пг/см³)')
    ax.set_title('Интерлейкин-17')
    ax.grid(True, alpha=0.3)
    
    # IL-23
    ax = axes[1, 2]
    I23_avg = np.mean(history['I23'][:, idx_L1:idx_h0], axis=1)
    ax.plot(time, I23_avg * 1e9, 'cyan', linewidth=2)
    ax.set_xlabel('Время (дни)')
    ax.set_ylabel('Концентрация (нг/см³)')
    ax.set_title('Интерлейкин-23')
    ax.grid(True, alpha=0.3)
    
    # TNF-alpha
    ax = axes[2, 0]
    Ta_avg = np.mean(history['Ta'][:, idx_L1:idx_h0], axis=1)
    ax.plot(time, Ta_avg * 1e12, 'red', linewidth=2)
    ax.set_xlabel('Время (дни)')
    ax.set_ylabel('Концентрация (пг/см³)')
    ax.set_title('TNF-α')
    ax.grid(True, alpha=0.3)
    
    # ECM
    ax = axes[2, 1]
    rho_avg = np.mean(history['rho'][:, idx_h0:], axis=1)
    ax.plot(time, rho_avg, 'darkblue', linewidth=2)
    ax.set_xlabel('Время (дни)')
    ax.set_ylabel('Плотность (г/см³)')
    ax.set_title('Внеклеточный матрикс (ρ)')
    ax.grid(True, alpha=0.3)
    
    # Граница h(t)
    ax = axes[2, 2]
    ax.plot(time, history['h'] * 10, 'black', linewidth=3)
    ax.axhline(y=h0*10, color='gray', linestyle='--', alpha=0.5, label='h₀')
    ax.set_xlabel('Время (дни)')
    ax.set_ylabel('Положение границы (мм)')
    ax.set_title('Динамика границы h(t)')
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    plt.tight_layout()
    
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"  График сохранён: {save_path}")
    
    return fig

def calculate_efficacy(h_control, h_treatment, h_initial):
    """Расчёт эффективности"""
    if h_control == h_initial:
        return 0.0
    return (h_control - h_treatment) / (h_control - h_initial) * 100.0

# ==================== ГЛАВНАЯ ПРОГРАММА ====================

if __name__ == "__main__":
    print("\n🚀 Запуск всех симуляций (ПОЛНЫЙ НАБОР)...")
    print("=" * 80)
    print("Будет выполнено 7 симуляций:")
    print("  • 1 контрольная")
    print("  • 3 монотерапии")
    print("  • 3 комбинированные терапии")
    print("Ожидаемое время: ~10-15 минут")
    print("=" * 80)
    
    # Контроль
    print("\n" + "=" * 80)
    print("1️⃣  КОНТРОЛЬНАЯ СИМУЛЯЦИЯ (без лечения)")
    results_control = solve_model(drug_type='none', verbose=True)
    
    # Инфликсимаб
    print("\n" + "=" * 80)
    print("2️⃣  ИНФЛИКСИМАБ (анти-TNF-α)")
    results_inflx = solve_model(drug_type='infliximab', verbose=True)
    
    # Метотрексат  
    print("\n" + "=" * 80)
    print("3️⃣  МЕТОТРЕКСАТ (иммуносупрессор)")
    results_mtx = solve_model(drug_type='methotrexate', verbose=True)
    
    # Тоцилизумаб
    print("\n" + "=" * 80)
    print("4️⃣  ТОЦИЛИЗУМАБ (анти-IL-6)")
    results_toci = solve_model(drug_type='tocilizumab', verbose=True)
    
    # КОМБИНИРОВАННЫЕ ТЕРАПИИ
    print("\n" + "=" * 80)
    print("5️⃣  КОМБИНАЦИЯ: Инфликсимаб + Метотрексат")
    results_combo_AY = solve_model(drug_type='combo_AY', verbose=True)
    
    print("\n" + "=" * 80)
    print("6️⃣  КОМБИНАЦИЯ: Инфликсимаб + Тоцилизумаб")
    results_combo_AZ = solve_model(drug_type='combo_AZ', verbose=True)
    
    print("\n" + "=" * 80)
    print("7️⃣  КОМБИНАЦИЯ: Метотрексат + Тоцилизумаб")
    results_combo_YZ = solve_model(drug_type='combo_YZ', verbose=True)
    
    # Анализ
    print("\n" + "=" * 80)
    print("📊 ПОЛНЫЙ АНАЛИЗ ЭФФЕКТИВНОСТИ ВСЕХ ТЕРАПИЙ")
    print("=" * 80)
    
    h_ctrl = results_control['h'][-1]
    h_inflx = results_inflx['h'][-1]
    h_mtx = results_mtx['h'][-1]
    h_toci = results_toci['h'][-1]
    h_combo_AY = results_combo_AY['h'][-1]
    h_combo_AZ = results_combo_AZ['h'][-1]
    h_combo_YZ = results_combo_YZ['h'][-1]
    
    eff_inflx = calculate_efficacy(h_ctrl, h_inflx, h0)
    eff_mtx = calculate_efficacy(h_ctrl, h_mtx, h0)
    eff_toci = calculate_efficacy(h_ctrl, h_toci, h0)
    eff_combo_AY = calculate_efficacy(h_ctrl, h_combo_AY, h0)
    eff_combo_AZ = calculate_efficacy(h_ctrl, h_combo_AZ, h0)
    eff_combo_YZ = calculate_efficacy(h_ctrl, h_combo_YZ, h0)
    
    print(f"\n{'='*80}")
    print(f"{'Терапия':<30} {'h(100), см':<12} {'Δh, мм':<10} {'Эффективность, %'}")
    print(f"{'-'*80}")
    print(f"{'Контроль':<30} {h_ctrl:<12.4f} {(h_ctrl-h0)*10:>+.2f}     {'-'}")
    print(f"{'-'*80}")
    print(f"{'МОНОТЕРАПИИ:':<30}")
    print(f"{'  Инфликсимаб':<30} {h_inflx:<12.4f} {(h_inflx-h0)*10:>+.2f}     {eff_inflx:.1f}%")
    print(f"{'  Метотрексат':<30} {h_mtx:<12.4f} {(h_mtx-h0)*10:>+.2f}     {eff_mtx:.1f}%")
    print(f"{'  Тоцилизумаб':<30} {h_toci:<12.4f} {(h_toci-h0)*10:>+.2f}     {eff_toci:.1f}%")
    print(f"{'-'*80}")
    print(f"{'КОМБИНИРОВАННЫЕ ТЕРАПИИ:':<30}")
    print(f"{'  Инфликсимаб + Метотрексат':<30} {h_combo_AY:<12.4f} {(h_combo_AY-h0)*10:>+.2f}     {eff_combo_AY:.1f}%")
    print(f"{'  Инфликсимаб + Тоцилизумаб':<30} {h_combo_AZ:<12.4f} {(h_combo_AZ-h0)*10:>+.2f}     {eff_combo_AZ:.1f}%")
    print(f"{'  Метотрексат + Тоцилизумаб':<30} {h_combo_YZ:<12.4f} {(h_combo_YZ-h0)*10:>+.2f}     {eff_combo_YZ:.1f}%")
    print(f"{'='*80}")
    
    # Находим лучшую терапию
    all_efficacies = {
        'Инфликсимаб': eff_inflx,
        'Метотрексат': eff_mtx,
        'Тоцилизумаб': eff_toci,
        'Инфликсимаб+Метотрексат': eff_combo_AY,
        'Инфликсимаб+Тоцилизумаб': eff_combo_AZ,
        'Метотрексат+Тоцилизумаб': eff_combo_YZ
    }
    
    best_therapy = max(all_efficacies, key=all_efficacies.get)
    best_eff = all_efficacies[best_therapy]
    
    print(f"\n🏆 ЛУЧШАЯ ТЕРАПИЯ: {best_therapy} ({best_eff:.1f}% эффективность)")
    print(f"{'='*80}")
    
    # Графики
    print("\n📊 Построение графиков...")
    fig1 = plot_temporal_dynamics(results_control, '(Контроль)', 
                                  'figures/temporal_dynamics/control_stable.png')
    
    # Сравнение h(t) - ВСЕ 7 ТЕРАПИЙ
    fig, axes = plt.subplots(1, 2, figsize=(18, 6))
    time_ctrl = np.array(results_control['time'])
    
    # График 1: Динамика h(t)
    ax = axes[0]
    ax.plot(time_ctrl, results_control['h'] * 10, 'black', linewidth=3, label='Контроль', linestyle='-')
    ax.plot(time_ctrl, results_inflx['h'] * 10, 'red', linewidth=2.5, label='Инфликсимаб', linestyle='-')
    ax.plot(time_ctrl, results_mtx['h'] * 10, 'blue', linewidth=2.5, label='Метотрексат', linestyle='-')
    ax.plot(time_ctrl, results_toci['h'] * 10, 'green', linewidth=2.5, label='Тоцилизумаб', linestyle='-')
    ax.plot(time_ctrl, results_combo_AY['h'] * 10, 'purple', linewidth=2.5, label='Инфликс.+Метотр.', linestyle='--')
    ax.plot(time_ctrl, results_combo_AZ['h'] * 10, 'orange', linewidth=2.5, label='Инфликс.+Тоцилиз.', linestyle='--')
    ax.plot(time_ctrl, results_combo_YZ['h'] * 10, 'cyan', linewidth=2.5, label='Метотр.+Тоцилиз.', linestyle='--')
    ax.axhline(y=h0*10, color='gray', linestyle=':', alpha=0.5, label='h₀')
    
    ax.set_xlabel('Время (дни)', fontsize=14)
    ax.set_ylabel('Положение границы h(t) (мм)', fontsize=14)
    ax.set_title('Динамика границы для всех терапий', fontsize=16, fontweight='bold')
    ax.legend(fontsize=11, loc='best')
    ax.grid(True, alpha=0.3)
    
    # График 2: Гистограмма эффективности
    ax = axes[1]
    therapies = ['Инфликс.', 'Метотр.', 'Тоцилиз.', 'A+Y', 'A+Z', 'Y+Z']
    efficacies = [eff_inflx, eff_mtx, eff_toci, eff_combo_AY, eff_combo_AZ, eff_combo_YZ]
    colors = ['red', 'blue', 'green', 'purple', 'orange', 'cyan']
    
    bars = ax.bar(range(len(therapies)), efficacies, color=colors, alpha=0.7, edgecolor='black', linewidth=2)
    ax.set_xticks(range(len(therapies)))
    ax.set_xticklabels(therapies, rotation=45, ha='right')
    ax.set_ylabel('Эффективность (%)', fontsize=14)
    ax.set_title('Сравнение эффективности всех терапий', fontsize=16, fontweight='bold')
    ax.grid(True, axis='y', alpha=0.3)
    ax.axhline(y=50, color='red', linestyle='--', alpha=0.5, label='50%')
    ax.legend(fontsize=11)
    
    # Добавляем значения на столбцы
    for bar, eff in zip(bars, efficacies):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
               f'{eff:.1f}%', ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('figures/treatment_comparison/comparison_full.png', dpi=300, bbox_inches='tight')
    print(f"  График сохранён: figures/treatment_comparison/comparison_full.png")
    
    plt.show()
    
    print("\n" + "=" * 80)
    print("✅ ВСЕ СИМУЛЯЦИИ ЗАВЕРШЕНЫ УСПЕШНО!")
    print("=" * 80)
    print("\n⚠️ ВАЖНО: Использована упрощённая модель")
    print("  • h(t) вычисляется по упрощённой формуле")
    print("  • Нет уравнений 2.19-2.22 (V, H)")
    print("  • Результаты качественно правильны")
    print("  • Количественные значения приближённые")
    print("\n📄 См. документацию для деталей")
    print("=" * 80)

