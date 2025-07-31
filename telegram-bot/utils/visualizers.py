"""
Функции для создания визуализаций и графиков
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import io
import base64
from pathlib import Path

# Настройка стиля для русского языка
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

def create_revenue_chart(data: List[Dict[str, Any]], title: str = "Выручка по каналам") -> str:
    """
    Создание столбчатой диаграммы выручки по каналам
    
    Args:
        data: Список словарей с данными каналов
        title: Заголовок графика
    
    Returns:
        Путь к созданному файлу изображения
    """
    # Подготовка данных
    channels = [item['name'] for item in data]
    revenues = [item['revenue'] for item in data]
    
    # Создание графика
    plt.figure(figsize=(12, 8))
    colors = plt.cm.Set3(range(len(channels)))
    
    bars = plt.bar(channels, revenues, color=colors)
    
    # Настройка графика
    plt.title(title, fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Каналы', fontsize=12)
    plt.ylabel('Выручка (₽)', fontsize=12)
    
    # Поворот подписей по оси X
    plt.xticks(rotation=45, ha='right')
    
    # Добавление значений на столбцы
    for bar, revenue in zip(bars, revenues):
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                f'{revenue:,.0f}₽', ha='center', va='bottom', fontsize=10)
    
    # Форматирование оси Y
    plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1000:.0f}К'))
    
    # Сетка
    plt.grid(axis='y', alpha=0.3)
    
    # Плотная компоновка
    plt.tight_layout()
    
    # Сохранение
    filename = f"revenue_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    filepath = Path(f"charts/{filename}")
    filepath.parent.mkdir(exist_ok=True)
    
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close()
    
    return str(filepath)

def create_conversion_funnel(funnel_data: Dict[str, int], title: str = "Воронка конверсии") -> str:
    """
    Создание воронки конверсии
    
    Args:
        funnel_data: Словарь с данными воронки {'Показы': 10000, 'Клики': 500, ...}
        title: Заголовок графика
    
    Returns:
        Путь к созданному файлу изображения
    """
    stages = list(funnel_data.keys())
    values = list(funnel_data.values())
    
    # Создание графика
    plt.figure(figsize=(10, 8))
    
    # Цвета для каждого этапа
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
    
    # Создание воронки
    y_positions = range(len(stages))
    
    for i, (stage, value, color) in enumerate(zip(stages, values, colors)):
        # Ширина блока пропорциональна значению
        width = value / max(values)
        
        # Рисуем прямоугольник
        plt.barh(i, width, color=color, alpha=0.8, height=0.6)
        
        # Добавляем текст с названием этапа и значением
        plt.text(width/2, i, f'{stage}\n{value:,}', 
                ha='center', va='center', fontweight='bold', fontsize=11)
        
        # Добавляем процент конверсии (кроме первого этапа)
        if i > 0:
            conversion_rate = (value / values[i-1]) * 100
            plt.text(width + 0.05, i, f'{conversion_rate:.1f}%', 
                    va='center', fontsize=10, color='gray')
    
    # Настройка графика
    plt.title(title, fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Относительное количество', fontsize=12)
    
    # Убираем оси
    plt.gca().set_yticks([])
    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)
    plt.gca().spines['left'].set_visible(False)
    
    plt.tight_layout()
    
    # Сохранение
    filename = f"funnel_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    filepath = Path(f"charts/{filename}")
    filepath.parent.mkdir(exist_ok=True)
    
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close()
    
    return str(filepath)

def create_roi_heatmap(channels_data: List[Dict[str, Any]], title: str = "Тепловая карта ROI по каналам") -> str:
    """
    Создание тепловой карты ROI по каналам и времени
    
    Args:
        channels_data: Данные по каналам
        title: Заголовок графика
    
    Returns:
        Путь к созданному файлу изображения
    """
    # Подготовка данных для тепловой карты
    channels = [item['name'] for item in channels_data]
    metrics = ['ROI', 'Конверсия', 'CAC', 'LTV']
    
    # Создание матрицы данных
    data_matrix = []
    for channel in channels_data:
        row = [
            channel['roi'] * 100,  # ROI в процентах
            channel['conversion'] * 100,  # Конверсия в процентах
            channel['cac'] / 1000,  # CAC в тысячах рублей
            channel['ltv'] / 1000   # LTV в тысячах рублей
        ]
        data_matrix.append(row)
    
    # Создание DataFrame
    df = pd.DataFrame(data_matrix, index=channels, columns=metrics)
    
    # Создание тепловой карты
    plt.figure(figsize=(10, 8))
    
    # Нормализация данных для лучшего отображения
    df_normalized = df.copy()
    for col in df.columns:
        df_normalized[col] = (df[col] - df[col].min()) / (df[col].max() - df[col].min())
    
    sns.heatmap(df_normalized, annot=df, fmt='.1f', cmap='RdYlGn', 
                center=0.5, cbar_kws={'label': 'Нормализованные значения'})
    
    plt.title(title, fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Метрики', fontsize=12)
    plt.ylabel('Каналы', fontsize=12)
    
    plt.tight_layout()
    
    # Сохранение
    filename = f"heatmap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    filepath = Path(f"charts/{filename}")
    filepath.parent.mkdir(exist_ok=True)
    
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close()
    
    return str(filepath)

def create_segments_pie_chart(segments_data: List[Dict[str, Any]], title: str = "Распределение клиентов по сегментам") -> str:
    """
    Создание круговой диаграммы сегментов клиентов
    
    Args:
        segments_data: Данные по сегментам
        title: Заголовок графика
    
    Returns:
        Путь к созданному файлу изображения
    """
    # Подготовка данных
    labels = [f"{item['emoji']} {item['name']}" for item in segments_data]
    sizes = [item['count'] for item in segments_data]
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
    
    # Создание круговой диаграммы
    plt.figure(figsize=(10, 8))
    
    wedges, texts, autotexts = plt.pie(sizes, labels=labels, autopct='%1.1f%%', 
                                      colors=colors, startangle=90, textprops={'fontsize': 11})
    
    # Улучшение внешнего вида
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_weight('bold')
    
    plt.title(title, fontsize=16, fontweight='bold', pad=20)
    
    # Легенда с дополнительной информацией
    legend_labels = [f"{item['name']}: {item['count']} клиентов ({item['revenue']:,.0f}₽)" 
                    for item in segments_data]
    plt.legend(legend_labels, loc='center left', bbox_to_anchor=(1, 0.5))
    
    plt.axis('equal')
    plt.tight_layout()
    
    # Сохранение
    filename = f"segments_pie_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    filepath = Path(f"charts/{filename}")
    filepath.parent.mkdir(exist_ok=True)
    
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close()
    
    return str(filepath)

def create_trend_chart(data: List[Dict[str, Any]], title: str = "Динамика показателей") -> str:
    """
    Создание графика трендов по времени
    
    Args:
        data: Данные с временными метками
        title: Заголовок графика
    
    Returns:
        Путь к созданному файлу изображения
    """
    # Подготовка данных
    dates = [datetime.strptime(item['date'], '%Y-%m-%d') for item in data]
    revenues = [item['revenue'] for item in data]
    leads = [item['leads'] for item in data]
    
    # Создание графика с двумя осями Y
    fig, ax1 = plt.subplots(figsize=(12, 8))
    
    # График выручки
    color1 = '#1f77b4'
    ax1.set_xlabel('Дата', fontsize=12)
    ax1.set_ylabel('Выручка (₽)', color=color1, fontsize=12)
    line1 = ax1.plot(dates, revenues, color=color1, linewidth=2, marker='o', label='Выручка')
    ax1.tick_params(axis='y', labelcolor=color1)
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1000:.0f}К'))
    
    # Вторая ось для лидов
    ax2 = ax1.twinx()
    color2 = '#ff7f0e'
    ax2.set_ylabel('Количество лидов', color=color2, fontsize=12)
    line2 = ax2.plot(dates, leads, color=color2, linewidth=2, marker='s', label='Лиды')
    ax2.tick_params(axis='y', labelcolor=color2)
    
    # Форматирование оси X
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m'))
    ax1.xaxis.set_major_locator(mdates.DayLocator(interval=7))
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
    
    # Заголовок и легенда
    plt.title(title, fontsize=16, fontweight='bold', pad=20)
    
    # Объединенная легенда
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    
    # Сетка
    ax1.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Сохранение
    filename = f"trend_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    filepath = Path(f"charts/{filename}")
    filepath.parent.mkdir(exist_ok=True)
    
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close()
    
    return str(filepath)

def create_forecast_chart(historical_data: List[float], forecast_data: List[float], 
                         title: str = "Прогноз выручки") -> str:
    """
    Создание графика с прогнозом
    
    Args:
        historical_data: Исторические данные
        forecast_data: Прогнозные данные
        title: Заголовок графика
    
    Returns:
        Путь к созданному файлу изображения
    """
    # Подготовка временных меток
    total_periods = len(historical_data) + len(forecast_data)
    dates = [datetime.now() - timedelta(days=30*(total_periods-i-1)) for i in range(total_periods)]
    
    historical_dates = dates[:len(historical_data)]
    forecast_dates = dates[len(historical_data)-1:]  # Начинаем с последней исторической точки
    
    # Создание графика
    plt.figure(figsize=(12, 8))
    
    # Исторические данные
    plt.plot(historical_dates, historical_data, 'o-', color='#1f77b4', 
             linewidth=2, markersize=6, label='Исторические данные')
    
    # Прогнозные данные
    forecast_values = [historical_data[-1]] + forecast_data  # Начинаем с последнего исторического значения
    plt.plot(forecast_dates, forecast_values, 's--', color='#ff7f0e', 
             linewidth=2, markersize=6, label='Прогноз', alpha=0.7)
    
    # Доверительный интервал для прогноза
    forecast_upper = [val * 1.2 for val in forecast_values]
    forecast_lower = [val * 0.8 for val in forecast_values]
    plt.fill_between(forecast_dates, forecast_lower, forecast_upper, 
                     alpha=0.2, color='#ff7f0e', label='Доверительный интервал')
    
    # Вертикальная линия, разделяющая прошлое и будущее
    plt.axvline(x=historical_dates[-1], color='red', linestyle=':', alpha=0.7, label='Текущий момент')
    
    # Настройка графика
    plt.title(title, fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Период', fontsize=12)
    plt.ylabel('Выручка (₽)', fontsize=12)
    
    # Форматирование осей
    plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1000:.0f}К'))
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m.%Y'))
    
    # Поворот подписей дат
    plt.xticks(rotation=45)
    
    # Легенда и сетка
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Сохранение
    filename = f"forecast_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    filepath = Path(f"charts/{filename}")
    filepath.parent.mkdir(exist_ok=True)
    
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close()
    
    return str(filepath)

def create_comparison_chart(data1: List[float], data2: List[float], 
                          labels: List[str], title: str = "Сравнение показателей") -> str:
    """
    Создание сравнительной диаграммы
    
    Args:
        data1: Первый набор данных
        data2: Второй набор данных
        labels: Подписи для категорий
        title: Заголовок графика
    
    Returns:
        Путь к созданному файлу изображения
    """
    x = range(len(labels))
    width = 0.35
    
    plt.figure(figsize=(12, 8))
    
    # Создание столбцов
    bars1 = plt.bar([i - width/2 for i in x], data1, width, label='Текущий период', color='#1f77b4')
    bars2 = plt.bar([i + width/2 for i in x], data2, width, label='Предыдущий период', color='#ff7f0e')
    
    # Добавление значений на столбцы
    for bar in bars1:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                f'{height:,.0f}', ha='center', va='bottom', fontsize=9)
    
    for bar in bars2:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                f'{height:,.0f}', ha='center', va='bottom', fontsize=9)
    
    # Настройка графика
    plt.title(title, fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Каналы', fontsize=12)
    plt.ylabel('Значения', fontsize=12)
    plt.xticks(x, labels, rotation=45, ha='right')
    
    plt.legend()
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    
    # Сохранение
    filename = f"comparison_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    filepath = Path(f"charts/{filename}")
    filepath.parent.mkdir(exist_ok=True)
    
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close()
    
    return str(filepath)

def create_dashboard_summary(channels_data: List[Dict[str, Any]], 
                           segments_data: List[Dict[str, Any]]) -> str:
    """
    Создание сводного дашборда с несколькими графиками
    
    Args:
        channels_data: Данные по каналам
        segments_data: Данные по сегментам
    
    Returns:
        Путь к созданному файлу изображения
    """
    # Создание фигуры с подграфиками
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    
    # 1. Выручка по каналам (столбчатая диаграмма)
    channels = [item['name'][:8] for item in channels_data[:6]]  # Ограничиваем длину названий
    revenues = [item['revenue'] for item in channels_data[:6]]
    
    bars = ax1.bar(channels, revenues, color=plt.cm.Set3(range(len(channels))))
    ax1.set_title('Выручка по каналам', fontweight='bold')
    ax1.set_ylabel('Выручка (₽)')
    ax1.tick_params(axis='x', rotation=45)
    
    # Значения на столбцах
    for bar, revenue in zip(bars, revenues):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                f'{revenue/1000:.0f}К', ha='center', va='bottom', fontsize=9)
    
    # 2. ROI по каналам (горизонтальная диаграмма)
    roi_values = [item['roi'] * 100 for item in channels_data[:6]]
    colors = ['green' if roi > 0 else 'red' for roi in roi_values]
    
    ax2.barh(channels, roi_values, color=colors, alpha=0.7)
    ax2.set_title('ROI по каналам (%)', fontweight='bold')
    ax2.set_xlabel('ROI (%)')
    ax2.axvline(x=0, color='black', linestyle='-', alpha=0.3)
    
    # 3. Сегменты клиентов (круговая диаграмма)
    segment_labels = [item['name'] for item in segments_data]
    segment_sizes = [item['count'] for item in segments_data]
    
    ax3.pie(segment_sizes, labels=segment_labels, autopct='%1.1f%%', startangle=90)
    ax3.set_title('Распределение клиентов', fontweight='bold')
    
    # 4. Конверсия по каналам (линейный график)
    conversion_values = [item['conversion'] * 100 for item in channels_data[:6]]
    
    ax4.plot(range(len(channels)), conversion_values, 'o-', linewidth=2, markersize=6)
    ax4.set_title('Конверсия по каналам (%)', fontweight='bold')
    ax4.set_ylabel('Конверсия (%)')
    ax4.set_xticks(range(len(channels)))
    ax4.set_xticklabels(channels, rotation=45)
    ax4.grid(True, alpha=0.3)
    
    # Общий заголовок
    fig.suptitle(f'Дашборд маркетинговой аналитики - {datetime.now().strftime("%d.%m.%Y")}', 
                fontsize=18, fontweight='bold')
    
    plt.tight_layout()
    plt.subplots_adjust(top=0.93)
    
    # Сохранение
    filename = f"dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    filepath = Path(f"charts/{filename}")
    filepath.parent.mkdir(exist_ok=True)
    
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close()
    
    return str(filepath)

def cleanup_old_charts(days_old: int = 7):
    """
    Очистка старых графиков
    
    Args:
        days_old: Возраст файлов в днях для удаления
    """
    charts_dir = Path("charts")
    if not charts_dir.exists():
        return
    
    cutoff_time = datetime.now() - timedelta(days=days_old)
    
    for chart_file in charts_dir.glob("*.png"):
        if chart_file.stat().st_mtime < cutoff_time.timestamp():
            chart_file.unlink()
            print(f"Удален старый график: {chart_file}")
