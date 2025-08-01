"""
Сервис визуализации для создания графиков и диаграмм
"""

import io
import logging
import matplotlib
matplotlib.use('Agg')  # Используем non-GUI backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.dates import DateFormatter
import seaborn as sns
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import numpy as np

# Настройка локализации для русского языка
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

logger = logging.getLogger(__name__)

class VisualizationService:
    """Сервис для создания графиков и диаграмм"""
    
    def __init__(self):
        # Настройка стиля
        sns.set_style("whitegrid")
        self.colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3', '#54A0FF']
    
    def create_channel_performance_chart(self, channels: List[Dict[str, Any]]) -> io.BytesIO:
        """
        Создание графика эффективности каналов
        
        Args:
            channels: Список каналов с метриками
            
        Returns:
            BytesIO объект с изображением графика
        """
        try:
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
            fig.suptitle('📊 Аналитика каналов привлечения', fontsize=16, fontweight='bold')
            
            if not channels:
                # Если нет данных
                for ax in [ax1, ax2, ax3, ax4]:
                    ax.text(0.5, 0.5, 'Нет данных для отображения', 
                           ha='center', va='center', transform=ax.transAxes, fontsize=12)
                    ax.set_xticks([])
                    ax.set_yticks([])
                
                buf = io.BytesIO()
                plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
                buf.seek(0)
                plt.close()
                return buf
            
            # Подготовка данных
            channel_names = [ch['name'] for ch in channels[:7]]  # Топ 7 каналов
            revenues = [ch.get('revenue', 0) for ch in channels[:7]]
            roi_values = [ch.get('roi', 0) * 100 for ch in channels[:7]]  # В процентах
            conversions = [ch.get('conversion_rate', 0) * 100 for ch in channels[:7]]  # В процентах
            cac_values = [ch.get('cac', 0) for ch in channels[:7]]
            
            # 1. Выручка по каналам (столбчатая диаграмма)
            bars1 = ax1.bar(channel_names, revenues, color=self.colors[:len(channel_names)])
            ax1.set_title('💰 Выручка по каналам', fontweight='bold')
            ax1.set_ylabel('Выручка, ₽')
            ax1.tick_params(axis='x', rotation=45)
            
            # Добавляем значения на столбцы
            for bar, value in zip(bars1, revenues):
                if value > 0:
                    ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(revenues)*0.01,
                            f'{value:,.0f}₽', ha='center', va='bottom', fontsize=9)
            
            # 2. ROI по каналам
            bars2 = ax2.bar(channel_names, roi_values, 
                           color=['green' if x > 0 else 'red' for x in roi_values])
            ax2.set_title('📈 ROI по каналам', fontweight='bold')
            ax2.set_ylabel('ROI, %')
            ax2.tick_params(axis='x', rotation=45)
            ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
            
            # Добавляем значения на столбцы
            for bar, value in zip(bars2, roi_values):
                ax2.text(bar.get_x() + bar.get_width()/2, 
                        bar.get_height() + (5 if value > 0 else -10),
                        f'{value:.1f}%', ha='center', 
                        va='bottom' if value > 0 else 'top', fontsize=9)
            
            # 3. Конверсия по каналам
            bars3 = ax3.bar(channel_names, conversions, color=self.colors[2:2+len(channel_names)])
            ax3.set_title('🎯 Конверсия по каналам', fontweight='bold')
            ax3.set_ylabel('Конверсия, %')
            ax3.tick_params(axis='x', rotation=45)
            
            # Добавляем значения на столбцы
            for bar, value in zip(bars3, conversions):
                if value > 0:
                    ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(conversions)*0.01,
                            f'{value:.1f}%', ha='center', va='bottom', fontsize=9)
            
            # 4. CAC по каналам
            bars4 = ax4.bar(channel_names, cac_values, color=self.colors[4:4+len(channel_names)])
            ax4.set_title('💸 CAC по каналам', fontweight='bold')
            ax4.set_ylabel('CAC, ₽')
            ax4.tick_params(axis='x', rotation=45)
            
            # Добавляем значения на столбцы
            for bar, value in zip(bars4, cac_values):
                if value > 0:
                    ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(cac_values)*0.01,
                            f'{value:,.0f}₽', ha='center', va='bottom', fontsize=9)
            
            plt.tight_layout()
            
            # Сохраняем график в BytesIO
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            buf.seek(0)
            plt.close()
            
            return buf
            
        except Exception as e:
            logger.error(f"Ошибка создания графика каналов: {e}")
            return self._create_error_chart("Ошибка создания графика каналов")
    
    def create_segments_pie_chart(self, segments: List[Dict[str, Any]]) -> io.BytesIO:
        """
        Создание круговой диаграммы сегментов клиентов
        
        Args:
            segments: Список сегментов клиентов
            
        Returns:
            BytesIO объект с изображением диаграммы
        """
        try:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7))
            fig.suptitle('👥 Анализ сегментов клиентов', fontsize=16, fontweight='bold')
            
            if not segments:
                # Если нет данных
                for ax in [ax1, ax2]:
                    ax.text(0.5, 0.5, 'Нет данных для отображения', 
                           ha='center', va='center', transform=ax.transAxes, fontsize=12)
                    ax.set_xticks([])
                    ax.set_yticks([])
                
                buf = io.BytesIO()
                plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
                buf.seek(0)
                plt.close()
                return buf
            
            # Подготовка данных
            segment_names = [s['segment'] for s in segments]
            client_counts = [s.get('clients_count', 0) for s in segments]
            revenues = [s.get('avg_revenue', 0) for s in segments]
            
            # 1. Круговая диаграмма по количеству клиентов
            if sum(client_counts) > 0:
                wedges1, texts1, autotexts1 = ax1.pie(
                    client_counts, 
                    labels=segment_names,
                    autopct='%1.1f%%',
                    colors=self.colors[:len(segments)],
                    startangle=90
                )
                ax1.set_title('Распределение клиентов по сегментам', fontweight='bold')
                
                # Улучшаем читаемость текста
                for autotext in autotexts1:
                    autotext.set_color('white')
                    autotext.set_fontweight('bold')
            else:
                ax1.text(0.5, 0.5, 'Нет данных о клиентах', 
                        ha='center', va='center', transform=ax1.transAxes)
            
            # 2. Средняя выручка по сегментам
            if revenues and any(r > 0 for r in revenues):
                bars = ax2.bar(segment_names, revenues, color=self.colors[:len(segments)])
                ax2.set_title('Средняя выручка по сегментам', fontweight='bold')
                ax2.set_ylabel('Средняя выручка, ₽')
                ax2.tick_params(axis='x', rotation=45)
                
                # Добавляем значения на столбцы
                for bar, value in zip(bars, revenues):
                    if value > 0:
                        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(revenues)*0.01,
                                f'{value:,.0f}₽', ha='center', va='bottom', fontsize=9)
            else:
                ax2.text(0.5, 0.5, 'Нет данных о выручке', 
                        ha='center', va='center', transform=ax2.transAxes)
            
            plt.tight_layout()
            
            # Сохраняем график в BytesIO
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            buf.seek(0)
            plt.close()
            
            return buf
            
        except Exception as e:
            logger.error(f"Ошибка создания диаграммы сегментов: {e}")
            return self._create_error_chart("Ошибка создания диаграммы сегментов")
    
    def create_forecast_chart(self, forecast_data: Dict[str, Any]) -> io.BytesIO:
        """
        Создание графика прогноза выручки
        
        Args:
            forecast_data: Данные прогноза выручки
            
        Returns:
            BytesIO объект с изображением графика
        """
        try:
            fig, ax = plt.subplots(1, 1, figsize=(12, 7))
            fig.suptitle('📈 Прогноз выручки', fontsize=16, fontweight='bold')
            
            forecast = forecast_data.get('forecast', [])
            
            if not forecast:
                ax.text(0.5, 0.5, 'Нет данных для прогноза', 
                       ha='center', va='center', transform=ax.transAxes, fontsize=12)
                ax.set_xticks([])
                ax.set_yticks([])
                
                buf = io.BytesIO()
                plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
                buf.seek(0)
                plt.close()
                return buf
            
            # Подготовка данных
            months = [f['month_name'] for f in forecast]
            revenues = [f['revenue'] for f in forecast]
            seasonal_coeffs = [f['seasonal_coefficient'] for f in forecast]
            
            # Основной график выручки
            line1 = ax.plot(months, revenues, marker='o', linewidth=3, 
                           markersize=8, color='#4ECDC4', label='Прогноз выручки')
            
            # Заливка под графиком
            ax.fill_between(months, revenues, alpha=0.3, color='#4ECDC4')
            
            # Добавляем значения на точки
            for i, (month, revenue) in enumerate(zip(months, revenues)):
                ax.annotate(f'{revenue:,.0f}₽', 
                           (i, revenue), 
                           textcoords="offset points", 
                           xytext=(0,10), 
                           ha='center', 
                           fontsize=10,
                           fontweight='bold')
            
            ax.set_title(f'Прогноз на {len(forecast)} месяца вперёд', fontweight='bold')
            ax.set_ylabel('Выручка, ₽')
            ax.set_xlabel('Месяц')
            ax.tick_params(axis='x', rotation=45)
            ax.grid(True, alpha=0.3)
            
            # Добавляем информацию о методологии
            methodology = forecast_data.get('methodology', '')
            if methodology:
                ax.text(0.02, 0.98, f'Методология: {methodology}', 
                       transform=ax.transAxes, fontsize=9, 
                       verticalalignment='top', 
                       bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue", alpha=0.7))
            
            # Среднее значение
            avg_forecast = sum(revenues) / len(revenues)
            ax.axhline(y=avg_forecast, color='red', linestyle='--', alpha=0.7, 
                      label=f'Среднее: {avg_forecast:,.0f}₽')
            
            ax.legend()
            plt.tight_layout()
            
            # Сохраняем график в BytesIO
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            buf.seek(0)
            plt.close()
            
            return buf
            
        except Exception as e:
            logger.error(f"Ошибка создания графика прогноза: {e}")
            return self._create_error_chart("Ошибка создания графика прогноза")
    
    def create_trends_chart(self, daily_data: List[Dict[str, Any]]) -> io.BytesIO:
        """
        Создание графика трендов (лиды, клиенты, выручка по дням)
        
        Args:
            daily_data: Данные по дням
            
        Returns:
            BytesIO объект с изображением графика
        """
        try:
            fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10))
            fig.suptitle('📊 Динамика ключевых метрик', fontsize=16, fontweight='bold')
            
            if not daily_data:
                for ax in [ax1, ax2, ax3]:
                    ax.text(0.5, 0.5, 'Нет данных для отображения', 
                           ha='center', va='center', transform=ax.transAxes, fontsize=12)
                    ax.set_xticks([])
                    ax.set_yticks([])
                
                buf = io.BytesIO()
                plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
                buf.seek(0)
                plt.close()
                return buf
            
            # Подготовка данных
            dates = [datetime.strptime(d['date'], '%Y-%m-%d') for d in daily_data]
            leads = [d.get('new_leads', 0) for d in daily_data]
            clients = [d.get('total_clients', 0) for d in daily_data]
            revenues = [d.get('revenue', 0) for d in daily_data]
            
            # 1. График лидов
            ax1.plot(dates, leads, marker='o', color='#FF6B6B', linewidth=2, markersize=6)
            ax1.set_title('🎯 Новые лиды по дням', fontweight='bold')
            ax1.set_ylabel('Количество лидов')
            ax1.grid(True, alpha=0.3)
            
            # 2. График клиентов
            ax2.plot(dates, clients, marker='s', color='#4ECDC4', linewidth=2, markersize=6)
            ax2.set_title('👥 Общее количество клиентов', fontweight='bold')
            ax2.set_ylabel('Количество клиентов')
            ax2.grid(True, alpha=0.3)
            
            # 3. График выручки
            ax3.plot(dates, revenues, marker='^', color='#45B7D1', linewidth=2, markersize=6)
            ax3.set_title('💰 Выручка по дням', fontweight='bold')
            ax3.set_ylabel('Выручка, ₽')
            ax3.set_xlabel('Дата')
            ax3.grid(True, alpha=0.3)
            
            # Форматирование дат на всех графиках
            for ax in [ax1, ax2, ax3]:
                ax.xaxis.set_major_formatter(DateFormatter('%d.%m'))
                ax.tick_params(axis='x', rotation=45)
            
            plt.tight_layout()
            
            # Сохраняем график в BytesIO
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            buf.seek(0)
            plt.close()
            
            return buf
            
        except Exception as e:
            logger.error(f"Ошибка создания графика трендов: {e}")
            return self._create_error_chart("Ошибка создания графика трендов")
    
    def create_comparison_chart(self, channel1_data: Dict, channel2_data: Dict) -> io.BytesIO:
        """
        Создание сравнительного графика двух каналов
        
        Args:
            channel1_data: Данные первого канала
            channel2_data: Данные второго канала
            
        Returns:
            BytesIO объект с изображением графика
        """
        try:
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle('⚖️ Сравнение каналов', fontsize=16, fontweight='bold')
            
            channel1_name = channel1_data.get('name', 'Канал 1')
            channel2_name = channel2_data.get('name', 'Канал 2')
            
            # Подготовка данных для сравнения
            metrics = ['Выручка', 'ROI (%)', 'Конверсия (%)', 'CAC']
            channel1_values = [
                channel1_data.get('revenue', 0),
                channel1_data.get('roi', 0) * 100,
                channel1_data.get('conversion_rate', 0) * 100,
                channel1_data.get('cac', 0)
            ]
            channel2_values = [
                channel2_data.get('revenue', 0),
                channel2_data.get('roi', 0) * 100,
                channel2_data.get('conversion_rate', 0) * 100,
                channel2_data.get('cac', 0)
            ]
            
            x = np.arange(len(metrics))
            width = 0.35
            
            # Создаём столбчатую диаграмму сравнения
            bars1 = ax1.bar(x - width/2, channel1_values, width, label=channel1_name, color='#FF6B6B')
            bars2 = ax1.bar(x + width/2, channel2_values, width, label=channel2_name, color='#4ECDC4')
            
            ax1.set_title('Сравнение ключевых метрик', fontweight='bold')
            ax1.set_xticks(x)
            ax1.set_xticklabels(metrics)
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # Добавляем значения на столбцы
            for bars, values in [(bars1, channel1_values), (bars2, channel2_values)]:
                for bar, value in zip(bars, values):
                    if value != 0:
                        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(max(channel1_values), max(channel2_values))*0.01,
                                f'{value:,.0f}', ha='center', va='bottom', fontsize=8)
            
            # Радарная диаграмма (упрощённая версия)
            # Пока используем столбчатую диаграмму вместо радара
            
            # 2. ROI сравнение
            roi_data = [channel1_data.get('roi', 0) * 100, channel2_data.get('roi', 0) * 100]
            roi_colors = ['green' if x > 0 else 'red' for x in roi_data]
            bars_roi = ax2.bar([channel1_name, channel2_name], roi_data, color=roi_colors)
            ax2.set_title('ROI сравнение', fontweight='bold')
            ax2.set_ylabel('ROI, %')
            ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
            
            # 3. Конверсия сравнение
            conv_data = [channel1_data.get('conversion_rate', 0) * 100, channel2_data.get('conversion_rate', 0) * 100]
            bars_conv = ax3.bar([channel1_name, channel2_name], conv_data, color=['#45B7D1', '#96CEB4'])
            ax3.set_title('Конверсия сравнение', fontweight='bold')
            ax3.set_ylabel('Конверсия, %')
            
            # 4. CAC сравнение
            cac_data = [channel1_data.get('cac', 0), channel2_data.get('cac', 0)]
            bars_cac = ax4.bar([channel1_name, channel2_name], cac_data, color=['#FECA57', '#FF9FF3'])
            ax4.set_title('CAC сравнение', fontweight='bold')
            ax4.set_ylabel('CAC, ₽')
            
            plt.tight_layout()
            
            # Сохраняем график в BytesIO
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            buf.seek(0)
            plt.close()
            
            return buf
            
        except Exception as e:
            logger.error(f"Ошибка создания сравнительного графика: {e}")
            return self._create_error_chart("Ошибка создания сравнительного графика")
    
    def _create_error_chart(self, error_message: str) -> io.BytesIO:
        """Создание графика с сообщением об ошибке"""
        fig, ax = plt.subplots(1, 1, figsize=(8, 6))
        ax.text(0.5, 0.5, f'❌ {error_message}', 
               ha='center', va='center', transform=ax.transAxes, 
               fontsize=14, color='red')
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title('Ошибка генерации графика', fontweight='bold')
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        plt.close()
        
        return buf

# Глобальная переменная для сервиса визуализации
_visualization_service = None

def get_visualization_service() -> VisualizationService:
    """Получение экземпляра сервиса визуализации"""
    global _visualization_service
    if _visualization_service is None:
        _visualization_service = VisualizationService()
    return _visualization_service
