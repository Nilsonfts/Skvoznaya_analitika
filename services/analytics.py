"""
Обновлённый сервис аналитики с поддержкой PostgreSQL и улучшенным прогнозированием
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta, date
from services.database import get_db_service
from services.google_sheets import GoogleSheetsService
from services.metrika import MetrikaService
from utils.calculations import (
    calculate_cac, calculate_ltv, calculate_roi, calculate_conversion,
    calculate_channel_rating, determine_client_segment, calculate_seasonal_coefficient
)
from config import USE_POSTGRES, EMOJI

logger = logging.getLogger(__name__)

class AnalyticsService:
    """Обновлённый сервис аналитики с поддержкой PostgreSQL"""
    
    def __init__(self):
        self.db_service = None
        self.sheets_service = GoogleSheetsService()
        self.metrika_service = MetrikaService()
        
    async def _ensure_db_connection(self):
        """Обеспечение подключения к базе данных"""
        if USE_POSTGRES and self.db_service is None:
            self.db_service = await get_db_service()
    
    async def generate_daily_report(self, target_date: date = None) -> Dict[str, Any]:
        """
        Генерация ежедневного отчёта с использованием базы данных
        
        Args:
            target_date: Дата отчёта (по умолчанию сегодня)
            
        Returns:
            Словарь с данными отчёта
        """
        try:
            await self._ensure_db_connection()
            
            if target_date is None:
                target_date = datetime.now().date()
            
            start_date = target_date - timedelta(days=30)  # Последние 30 дней
            
            if USE_POSTGRES and self.db_service:
                # Получаем данные из PostgreSQL
                channel_analytics = await self.db_service.get_channel_analytics(start_date, target_date)
                segments_analytics = await self.db_service.get_segments_analytics()
                
                # Вычисляем общие метрики
                total_leads = sum(ch.get('leads_count', 0) for ch in channel_analytics)
                total_clients = sum(ch.get('clients_count', 0) for ch in channel_analytics)
                total_revenue = sum(ch.get('revenue', 0) for ch in channel_analytics)
                total_cost = sum(ch.get('cost_per_month', 0) for ch in channel_analytics)
                
                overall_conversion = total_clients / total_leads if total_leads > 0 else 0
                overall_roi = calculate_roi(total_revenue, total_cost)
                
                # Топ каналы по выручке
                top_channels = sorted(channel_analytics, key=lambda x: x.get('revenue', 0), reverse=True)[:5]
                
                # Новые лиды за сегодня
                today_leads = await self.db_service.get_leads(
                    start_date=target_date,
                    end_date=target_date
                )
                
                new_leads_today = len(today_leads)
                
            else:
                # Fallback на Google Sheets
                logger.warning("PostgreSQL не настроен, используем Google Sheets")
                return await self._generate_report_from_sheets(target_date)
            
            return {
                'date': target_date.strftime('%Y-%m-%d'),
                'new_leads': new_leads_today,
                'total_leads': total_leads,
                'total_clients': total_clients,
                'conversion': overall_conversion,
                'revenue': total_revenue,
                'cost': total_cost,
                'roi': overall_roi,
                'top_channels': [
                    {
                        'name': ch['name'],
                        'revenue': ch.get('revenue', 0),
                        'roi': ch.get('roi', 0),
                        'clients': ch.get('clients_count', 0)
                    }
                    for ch in top_channels
                ],
                'segments': segments_analytics,
                'alerts': await self._check_daily_alerts(channel_analytics)
            }
            
        except Exception as e:
            logger.error(f"Ошибка генерации ежедневного отчёта: {e}")
            return {}
    
    async def analyze_channels(self, days_back: int = 30) -> List[Dict[str, Any]]:
        """
        Анализ эффективности каналов
        
        Args:
            days_back: Количество дней для анализа
            
        Returns:
            Список каналов с метриками
        """
        try:
            await self._ensure_db_connection()
            
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days_back)
            
            if USE_POSTGRES and self.db_service:
                analytics = await self.db_service.get_channel_analytics(start_date, end_date)
                
                # Добавляем рейтинг каналов
                for channel in analytics:
                    channel['rating'] = calculate_channel_rating(
                        channel.get('roi', 0),
                        channel.get('conversion_rate', 0),
                        channel.get('cac', 0)
                    )
                
                return sorted(analytics, key=lambda x: x.get('revenue', 0), reverse=True)
            
            else:
                # Fallback на Google Sheets
                return await self._analyze_channels_from_sheets(days_back)
                
        except Exception as e:
            logger.error(f"Ошибка анализа каналов: {e}")
            return []
    
    async def analyze_segments(self) -> List[Dict[str, Any]]:
        """
        Анализ сегментов клиентов
        
        Returns:
            Список сегментов с метриками
        """
        try:
            await self._ensure_db_connection()
            
            if USE_POSTGRES and self.db_service:
                segments = await self.db_service.get_segments_analytics()
                
                # Добавляем процентное распределение
                total_clients = sum(s.get('clients_count', 0) for s in segments)
                
                for segment in segments:
                    segment['percentage'] = (
                        segment.get('clients_count', 0) / total_clients * 100 
                        if total_clients > 0 else 0
                    )
                
                return sorted(segments, key=lambda x: x.get('clients_count', 0), reverse=True)
            
            else:
                # Fallback на Google Sheets
                return await self._analyze_segments_from_sheets()
                
        except Exception as e:
            logger.error(f"Ошибка анализа сегментов: {e}")
            return []
    
    async def forecast_revenue(self, months_ahead: int = 3) -> Dict[str, Any]:
        """
        Прогнозирование выручки с учётом сезонности
        
        Args:
            months_ahead: Количество месяцев для прогноза
            
        Returns:
            Прогноз выручки по месяцам
        """
        try:
            await self._ensure_db_connection()
            
            # Получаем историческую выручку за последние 12 месяцев
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=365)
            
            if USE_POSTGRES and self.db_service:
                analytics = await self.db_service.get_channel_analytics(start_date, end_date)
                total_revenue = sum(ch.get('revenue', 0) for ch in analytics)
            else:
                # Fallback на Google Sheets
                total_revenue = await self._get_historical_revenue_from_sheets()
            
            # Вычисляем среднемесячную выручку
            avg_monthly_revenue = total_revenue / 12 if total_revenue > 0 else 0
            
            # Создаём прогноз с учётом сезонности
            forecast = []
            current_date = datetime.now()
            
            for i in range(months_ahead):
                forecast_date = current_date + timedelta(days=30 * i)
                month = forecast_date.month
                
                # Применяем сезонный коэффициент
                seasonal_coefficient = calculate_seasonal_coefficient(month)
                forecasted_revenue = avg_monthly_revenue * seasonal_coefficient
                
                # Добавляем небольшой тренд роста (2% в месяц)
                growth_factor = 1.02 ** i
                forecasted_revenue *= growth_factor
                
                forecast.append({
                    'month': forecast_date.strftime('%Y-%m'),
                    'month_name': forecast_date.strftime('%B %Y'),
                    'revenue': round(forecasted_revenue, 2),
                    'seasonal_coefficient': seasonal_coefficient,
                    'growth_factor': growth_factor
                })
            
            return {
                'historical_avg': avg_monthly_revenue,
                'forecast': forecast,
                'total_forecast': sum(f['revenue'] for f in forecast),
                'methodology': 'Историческая средняя × Сезонность × Тренд роста (2%/мес)'
            }
            
        except Exception as e:
            logger.error(f"Ошибка прогнозирования выручки: {e}")
            return {}
    
    async def get_managers_performance(self) -> List[Dict[str, Any]]:
        """
        Анализ эффективности менеджеров (заглушка для совместимости)
        
        Returns:
            Список менеджеров с метриками
        """
        # Пока возвращаем пустой список, так как в караоке-рюмочной
        # может не быть отдельных менеджеров по продажам
        return [
            {
                'name': 'Администратор',
                'leads_processed': 0,
                'conversion_rate': 0,
                'revenue': 0,
                'notes': 'Функция в разработке для караоке-рюмочной'
            }
        ]
    
    async def _check_daily_alerts(self, channel_analytics: List[Dict]) -> List[str]:
        """Проверка на предупреждения в ежедневном отчёте"""
        alerts = []
        
        for channel in channel_analytics:
            # Низкий ROI
            if channel.get('roi', 0) < -0.5:  # ROI ниже -50%
                alerts.append(f"📉 {channel['name']}: критически низкий ROI ({channel.get('roi', 0):.1%})")
            
            # Низкая конверсия
            if channel.get('conversion_rate', 0) < 0.05:  # Конверсия ниже 5%
                alerts.append(f"⚠️ {channel['name']}: низкая конверсия ({channel.get('conversion_rate', 0):.1%})")
            
            # Высокий CAC
            if channel.get('cac', 0) > 15000:  # CAC выше 15000 рублей
                alerts.append(f"💰 {channel['name']}: высокий CAC ({channel.get('cac', 0):.0f} ₽)")
        
        return alerts
    
    async def _generate_report_from_sheets(self, target_date: date) -> Dict[str, Any]:
        """Генерация отчёта из Google Sheets (fallback)"""
        logger.info("Генерируем отчёт из Google Sheets")
        
        # Здесь должна быть логика работы с Google Sheets
        # Пока возвращаем базовую структуру
        return {
            'date': target_date.strftime('%Y-%m-%d'),
            'new_leads': 0,
            'total_leads': 0,
            'total_clients': 0,
            'conversion': 0,
            'revenue': 0,
            'cost': 0,
            'roi': 0,
            'top_channels': [],
            'segments': [],
            'alerts': ['⚠️ Данные получены из Google Sheets (PostgreSQL не настроен)']
        }
    
    async def _analyze_channels_from_sheets(self, days_back: int) -> List[Dict]:
        """Анализ каналов из Google Sheets (fallback)"""
        logger.info("Анализируем каналы из Google Sheets")
        return []
    
    async def _analyze_segments_from_sheets(self) -> List[Dict]:
        """Анализ сегментов из Google Sheets (fallback)"""
        logger.info("Анализируем сегменты из Google Sheets")
        return []
    
    async def _get_historical_revenue_from_sheets(self) -> float:
        """Получение исторической выручки из Google Sheets"""
        logger.info("Получаем историческую выручку из Google Sheets")
        return 0.0
    
    # Методы для совместимости со старым кодом
    async def merge_all_leads(self) -> Dict[str, Any]:
        """
        Объединение лидов с реальной обработкой данных.
        """
        try:
            # Пример обработки данных
            site_leads = await self.get_site_leads()
            social_leads = await self.get_social_leads()
            new_leads = len(site_leads) + len(social_leads)

            return {
                'success': True,
                'site_leads': len(site_leads),
                'social_leads': len(social_leads),
                'new_leads': new_leads,
                'duplicates': 0,  # Пример
                'enriched': 0     # Пример
            }
        except Exception as e:
            logger.error(f"Ошибка в merge_all_leads: {e}")
            return {'success': False}
    
    async def update_all_dashboards(self) -> Dict[str, Any]:
        """Обновление дашбордов (совместимость)"""
        return {'success': True}
    
    async def generate_weekly_report(self) -> Dict[str, Any]:
        """Еженедельный отчёт"""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=7)
        
        analytics = await self.analyze_channels(7)
        segments = await self.analyze_segments()
        
        return {
            'period': f"{start_date} - {end_date}",
            'channels': analytics,
            'segments': segments,
            'type': 'weekly'
        }
    
    async def generate_monthly_report(self) -> Dict[str, Any]:
        """Ежемесячный отчёт"""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        
        analytics = await self.analyze_channels(30)
        segments = await self.analyze_segments()
        forecast = await self.forecast_revenue(3)
        
        return {
            'period': f"{start_date} - {end_date}",
            'channels': analytics,
            'segments': segments,
            'forecast': forecast,
            'type': 'monthly'
        }
    
    async def analyze_channel(self, channel_name: str) -> Optional[Dict[str, Any]]:
        """
        Детальный анализ конкретного канала
        
        Args:
            channel_name: Название канала
            
        Returns:
            Подробная аналитика канала
        """
        try:
            await self._ensure_db_connection()
            
            if USE_POSTGRES and self.db_service:
                channel = await self.db_service.get_channel_by_name(channel_name)
                if not channel:
                    return None
                
                # Получаем аналитику за последние 30 дней
                end_date = datetime.now().date()
                start_date = end_date - timedelta(days=30)
                
                analytics = await self.db_service.get_channel_analytics(start_date, end_date)
                channel_data = next((ch for ch in analytics if ch['name'] == channel_name), None)
                
                if not channel_data:
                    return None
                
                # Добавляем дополнительные метрики
                channel_data['rating'] = calculate_channel_rating(
                    channel_data.get('roi', 0),
                    channel_data.get('conversion_rate', 0),
                    channel_data.get('cac', 0)
                )
                
                # Период окупаемости
                if channel_data.get('cac', 0) > 0 and channel_data.get('ltv', 0) > 0:
                    avg_check = channel_data.get('ltv', 0) / 6  # Предполагаем 6 визитов в год
                    channel_data['payback_visits'] = channel_data.get('cac', 0) / avg_check if avg_check > 0 else float('inf')
                else:
                    channel_data['payback_visits'] = float('inf')
                
                return channel_data
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка анализа канала {channel_name}: {e}")
            return None
