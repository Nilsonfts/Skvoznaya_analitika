"""
Основной сервис аналитики - объединение лидов, расчет метрик, создание дашбордов
"""

import logging
import asyncio
import hashlib
import uuid
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
import re

from config import (
    CHANNEL_COSTS, SEGMENT_CONFIG, LTV_CONFIG, CHANNEL_MAPPING, 
    SHEETS_CONFIG, ALERTS_CONFIG, EMOJI
)
from services.google_sheets import GoogleSheetsService
from services.metrika import MetrikaService
from utils.calculations import (
    calculate_cac, calculate_ltv, calculate_roi, calculate_conversion,
    calculate_channel_rating, determine_client_segment
)
from utils.formatters import clean_phone, normalize_email, format_date

logger = logging.getLogger(__name__)

class AnalyticsService:
    def __init__(self):
        """Инициализация сервиса аналитики"""
        self.sheets_service = GoogleSheetsService()
        self.metrika_service = MetrikaService()
        logger.info("Сервис аналитики инициализирован")
    
    async def merge_all_leads(self) -> Dict[str, Any]:
        """Объединение всех лидов из разных источников"""
        try:
            logger.info("Начинаю объединение лидов")
            
            # Получение данных из источников
            site_leads = self.sheets_service.get_leads_from_site()
            social_leads = self.sheets_service.get_leads_from_social()
            guests_data = self.sheets_service.get_guests_data()
            
            # Получение существующих лидов для проверки дубликатов
            existing_leads = self.sheets_service.read_sheet_data(SHEETS_CONFIG['analytics'])
            existing_keys = set()
            
            for lead in existing_leads:
                key = self._generate_lead_key(lead.get('phone', ''), lead.get('email', ''))
                existing_keys.add(key)
            
            # Объединение и обработка лидов
            all_leads = []
            new_leads_count = 0
            duplicates_count = 0
            
            # Обработка лидов с сайта
            for lead in site_leads:
                processed_lead = self._process_lead(lead, guests_data)
                lead_key = self._generate_lead_key(processed_lead['phone'], processed_lead['email'])
                
                if lead_key not in existing_keys:
                    all_leads.append(processed_lead)
                    existing_keys.add(lead_key)
                    new_leads_count += 1
                else:
                    duplicates_count += 1
            
            # Обработка лидов из соцсетей
            for lead in social_leads:
                processed_lead = self._process_lead(lead, guests_data)
                lead_key = self._generate_lead_key(processed_lead['phone'], processed_lead['email'])
                
                if lead_key not in existing_keys:
                    # Генерация ID для отсутствующих полей
                    if not processed_lead['ga_client_id']:
                        processed_lead['ga_client_id'] = self._generate_client_id()
                    if not processed_lead['ym_client_id']:
                        processed_lead['ym_client_id'] = self._generate_client_id()
                    
                    all_leads.append(processed_lead)
                    existing_keys.add(lead_key)
                    new_leads_count += 1
                else:
                    duplicates_count += 1
            
            # Обогащение данными из Яндекс.Метрики
            enriched_count = 0
            if all_leads:
                metrika_data = await self.metrika_service.get_batch_client_metrics(all_leads)
                
                for lead in all_leads:
                    client_id = lead.get('ym_client_id', '')
                    if client_id in metrika_data:
                        lead.update({
                            'ym_visits': metrika_data[client_id]['visits'],
                            'ym_pageviews': metrika_data[client_id]['pageviews'],
                            'ym_bounce_rate': metrika_data[client_id]['bounce_rate'],
                            'ym_avg_duration': metrika_data[client_id]['avg_visit_duration']
                        })
                        enriched_count += 1
                    else:
                        lead.update({
                            'ym_visits': 0,
                            'ym_pageviews': 0,
                            'ym_bounce_rate': 0,
                            'ym_avg_duration': 0
                        })
            
            # Сохранение новых лидов
            if all_leads:
                success = self.sheets_service.append_sheet_data(SHEETS_CONFIG['analytics'], all_leads)
                if not success:
                    return {
                        'success': False,
                        'error': 'Ошибка сохранения данных в Google Sheets'
                    }
            
            logger.info(f"Объединение лидов завершено: {new_leads_count} новых, {duplicates_count} дубликатов")
            
            return {
                'success': True,
                'site_leads': len(site_leads),
                'social_leads': len(social_leads),
                'new_leads': new_leads_count,
                'duplicates': duplicates_count,
                'enriched': enriched_count
            }
            
        except Exception as e:
            logger.error(f"Ошибка объединения лидов: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _process_lead(self, lead: Dict[str, Any], guests_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Обработка и обогащение одного лида"""
        # Очистка и стандартизация данных
        processed_lead = {
            'lead_id': self._generate_lead_id(),
            'date': format_date(lead.get('date', '')),
            'name': lead.get('name', '').strip(),
            'phone': clean_phone(lead.get('phone', '')),
            'email': normalize_email(lead.get('email', '')),
            'utm_source': lead.get('utm_source', '').strip(),
            'utm_medium': lead.get('utm_medium', '').strip(),
            'utm_campaign': lead.get('utm_campaign', '').strip(),
            'utm_content': lead.get('utm_content', '').strip(),
            'utm_term': lead.get('utm_term', '').strip(),
            'ga_client_id': lead.get('ga_client_id', '').strip(),
            'ym_client_id': lead.get('ym_client_id', '').strip(),
            'form_name': lead.get('form_name', '').strip(),
            'button_text': lead.get('button_text', '').strip(),
            'source': lead.get('source', ''),
            'channel': self._determine_channel(lead),
            'status': 'Потенциальный',
            'segment': 'NEW',
            'visits_count': 0,
            'total_revenue': 0,
            'avg_check': 0,
            'first_visit_date': '',
            'last_visit_date': '',
            'ltv': 0,
            'days_since_first_visit': 0
        }
        
        # Обогащение данными о клиенте
        client_info = self._find_client_info(processed_lead, guests_data)
        if client_info:
            processed_lead.update({
                'status': 'Повторный' if client_info['visits_count'] > 1 else 'Новый',
                'segment': determine_client_segment(
                    client_info['visits_count'], 
                    client_info['total_revenue'],
                    client_info.get('visit_amounts')
                ),
                'visits_count': client_info['visits_count'],
                'total_revenue': client_info['total_revenue'],
                'avg_check': client_info['avg_check'],
                'first_visit_date': client_info['first_visit_date'],
                'last_visit_date': client_info['last_visit_date'],
                'ltv': calculate_ltv(
                    client_info['avg_check'], 
                    client_info['visits_count'],
                    client_info.get('visit_amounts')
                ),
                'days_since_first_visit': client_info['days_since_first_visit']
            })
        
        return processed_lead
    
    def _generate_lead_key(self, phone: str, email: str) -> str:
        """Генерация ключа для проверки дубликатов"""
        phone_clean = clean_phone(phone)
        email_clean = normalize_email(email)
        
        # Используем последние 10 цифр телефона + email в нижнем регистре
        phone_key = phone_clean[-10:] if len(phone_clean) >= 10 else phone_clean
        key = f"{phone_key}|{email_clean}"
        
        return hashlib.md5(key.encode()).hexdigest()
    
    def _generate_lead_id(self) -> str:
        """Генерация уникального ID лида"""
        # Получаем текущий максимальный номер из существующих лидов
        existing_leads = self.sheets_service.read_sheet_data(SHEETS_CONFIG['analytics'])
        max_num = 0
        
        for lead in existing_leads:
            lead_id = lead.get('lead_id', '')
            if lead_id.startswith('LEAD_'):
                try:
                    num = int(lead_id.replace('LEAD_', ''))
                    max_num = max(max_num, num)
                except ValueError:
                    continue
        
        return f"LEAD_{max_num + 1}"
    
    def _generate_client_id(self) -> str:
        """Генерация уникального Client ID"""
        return str(uuid.uuid4())
    
    def _determine_channel(self, lead: Dict[str, Any]) -> str:
        """Определение канала привлечения на основе UTM меток"""
        utm_source = lead.get('utm_source', '').lower().strip()
        utm_medium = lead.get('utm_medium', '').lower().strip()
        
        if not utm_source and not utm_medium:
            return 'Direct'
        
        # Проверяем маппинг каналов
        for key, channel in CHANNEL_MAPPING.items():
            if key in utm_source or key in utm_medium:
                return channel
        
        # Если не нашли точное соответствие, возвращаем Other
        return 'Other'
    
    def _find_client_info(self, lead: Dict[str, Any], guests_data: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Поиск информации о клиенте в данных Guests RP"""
        lead_phone = clean_phone(lead['phone'])
        lead_email = normalize_email(lead['email'])
        
        for guest in guests_data:
            guest_phone = clean_phone(guest.get('phone', ''))
            guest_email = normalize_email(guest.get('email', ''))
            
            # Сравнение по последним 10 цифрам телефона или email
            phone_match = (len(lead_phone) >= 10 and len(guest_phone) >= 10 and 
                          lead_phone[-10:] == guest_phone[-10:])
            email_match = (lead_email and guest_email and lead_email == guest_email)
            
            if phone_match or email_match:
                # Извлекаем информацию о клиенте
                visits_count = int(guest.get('visits_count', 0) or 0)
                total_revenue = float(guest.get('total_revenue', 0) or 0)
                visit_amounts = guest.get('visit_amounts', [])
                
                # Если у нас есть детализация по визитам, используем её
                if visit_amounts:
                    # Ограничиваем количество визитов до 6 в год для LTV
                    limited_visit_amounts = visit_amounts[:6]
                    avg_check = sum(limited_visit_amounts) / len(limited_visit_amounts) if limited_visit_amounts else 0
                else:
                    avg_check = total_revenue / visits_count if visits_count > 0 else 0
                
                first_visit_date = guest.get('first_visit_date', '')
                last_visit_date = guest.get('last_visit_date', '')
                
                # Расчет дней с первого визита
                days_since_first_visit = 0
                if first_visit_date:
                    try:
                        first_date = datetime.strptime(first_visit_date, '%Y-%m-%d')
                        days_since_first_visit = (datetime.now() - first_date).days
                    except ValueError:
                        pass
                
                return {
                    'visits_count': visits_count,
                    'total_revenue': total_revenue,
                    'avg_check': avg_check,
                    'first_visit_date': first_visit_date,
                    'last_visit_date': last_visit_date,
                    'days_since_first_visit': days_since_first_visit,
                    'visit_amounts': visit_amounts  # Добавляем детализацию визитов
                }
        
        return None
    
    async def analyze_channels(self) -> List[Dict[str, Any]]:
        """Анализ эффективности каналов"""
        try:
            leads_data = self.sheets_service.read_sheet_data(SHEETS_CONFIG['analytics'])
            
            if not leads_data:
                return []
            
            # Группировка по каналам
            channels_stats = {}
            
            for lead in leads_data:
                channel = lead.get('channel', 'Other')
                
                if channel not in channels_stats:
                    channels_stats[channel] = {
                        'name': channel,
                        'leads': 0,
                        'clients': 0,
                        'new_clients': 0,
                        'vip_clients': 0,
                        'revenue': 0,
                        'total_visits': 0
                    }
                
                stats = channels_stats[channel]
                stats['leads'] += 1
                
                revenue = float(lead.get('total_revenue', 0) or 0)
                visits = int(lead.get('visits_count', 0) or 0)
                segment = lead.get('segment', 'NEW')
                
                if revenue > 0:
                    stats['clients'] += 1
                    stats['revenue'] += revenue
                    stats['total_visits'] += visits
                    
                    if segment == 'VIP':
                        stats['vip_clients'] += 1
                    elif visits == 1:
                        stats['new_clients'] += 1
            
            # Расчет метрик
            channels_analysis = []
            
            for channel, stats in channels_stats.items():
                cost = CHANNEL_COSTS.get(channel, 0)
                
                conversion = calculate_conversion(stats['clients'], stats['leads'])
                cac = calculate_cac(cost, stats['clients'])
                avg_check = stats['revenue'] / stats['clients'] if stats['clients'] > 0 else 0
                ltv = calculate_ltv(avg_check, stats['total_visits'] / stats['clients'] if stats['clients'] > 0 else 0)
                roi = calculate_roi(stats['revenue'], cost)
                rating = calculate_channel_rating(roi, conversion, cac)
                
                channels_analysis.append({
                    'name': channel,
                    'leads': stats['leads'],
                    'clients': stats['clients'],
                    'conversion': conversion,
                    'new_clients': stats['new_clients'],
                    'vip_clients': stats['vip_clients'],
                    'revenue': stats['revenue'],
                    'avg_check': avg_check,
                    'cac': cac,
                    'ltv': ltv,
                    'roi': roi,
                    'rating': rating,
                    'payback_visits': cac / avg_check if avg_check > 0 else 0
                })
            
            # Сортировка по ROI
            channels_analysis.sort(key=lambda x: x['roi'], reverse=True)
            
            return channels_analysis
            
        except Exception as e:
            logger.error(f"Ошибка анализа каналов: {e}")
            return []
    
    async def analyze_channel(self, channel_name: str) -> Optional[Dict[str, Any]]:
        """Детальный анализ конкретного канала"""
        try:
            channels_data = await self.analyze_channels()
            
            for channel in channels_data:
                if channel['name'].lower() == channel_name.lower():
                    # Дополнительные данные для детального анализа
                    leads_data = self.sheets_service.read_sheet_data(SHEETS_CONFIG['analytics'])
                    
                    channel_leads = [lead for lead in leads_data if lead.get('channel', '').lower() == channel_name.lower()]
                    
                    # Анализ временных показателей
                    last_activity = None
                    if channel_leads:
                        dates = [lead.get('date', '') for lead in channel_leads if lead.get('date')]
                        if dates:
                            try:
                                last_activity = max([datetime.strptime(d.split(' ')[0], '%Y-%m-%d') for d in dates if d])
                                last_activity = last_activity.strftime('%d.%m.%Y')
                            except ValueError:
                                last_activity = 'Недавно'
                    
                    # Получение данных из Яндекс.Метрики
                    end_date = datetime.now().strftime('%Y-%m-%d')
                    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                    metrika_data = await self.metrika_service.get_channel_metrics(channel_name, start_date, end_date)
                    
                    return {
                        **channel,
                        'total_leads': channel['leads'],
                        'last_activity': last_activity or 'Нет данных',
                        'metrika_data': metrika_data if metrika_data['visits'] > 0 else None
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка анализа канала {channel_name}: {e}")
            return None
    
    async def analyze_segments(self) -> List[Dict[str, Any]]:
        """Анализ сегментов клиентов"""
        try:
            leads_data = self.sheets_service.read_sheet_data(SHEETS_CONFIG['analytics'])
            
            if not leads_data:
                return []
            
            # Группировка по сегментам
            segments_stats = {}
            
            for segment_name, config in SEGMENT_CONFIG.items():
                segments_stats[segment_name] = {
                    'name': segment_name,
                    'emoji': config['emoji'],
                    'count': 0,
                    'revenue': 0,
                    'total_visits': 0
                }
            
            for lead in leads_data:
                segment = lead.get('segment', 'NEW')
                revenue = float(lead.get('total_revenue', 0) or 0)
                visits = int(lead.get('visits_count', 0) or 0)
                
                if segment in segments_stats:
                    segments_stats[segment]['count'] += 1
                    segments_stats[segment]['revenue'] += revenue
                    segments_stats[segment]['total_visits'] += visits
            
            # Расчет средних показателей
            segments_analysis = []
            
            for segment_name, stats in segments_stats.items():
                avg_check = stats['revenue'] / stats['count'] if stats['count'] > 0 else 0
                avg_visits = stats['total_visits'] / stats['count'] if stats['count'] > 0 else 0
                
                segments_analysis.append({
                    'name': segment_name,
                    'emoji': stats['emoji'],
                    'count': stats['count'],
                    'revenue': stats['revenue'],
                    'avg_check': avg_check,
                    'avg_visits': avg_visits
                })
            
            # Сортировка по приоритету сегментов
            segment_order = ['VIP', 'REGULAR', 'RETURNING', 'NEW']
            segments_analysis.sort(key=lambda x: segment_order.index(x['name']) if x['name'] in segment_order else 999)
            
            return segments_analysis
            
        except Exception as e:
            logger.error(f"Ошибка анализа сегментов: {e}")
            return []
    
    async def analyze_managers(self) -> List[Dict[str, Any]]:
        """Анализ эффективности менеджеров"""
        try:
            leads_data = self.sheets_service.read_sheet_data(SHEETS_CONFIG['analytics'])
            
            if not leads_data:
                return []
            
            # Проверяем наличие колонки "Менеджер"
            if not any('manager' in lead or 'менеджер' in lead for lead in leads_data):
                return []
            
            # Группировка по менеджерам
            managers_stats = {}
            
            for lead in leads_data:
                manager = lead.get('manager', lead.get('менеджер', 'Не указан')).strip()
                
                if manager not in managers_stats:
                    managers_stats[manager] = {
                        'name': manager,
                        'leads': 0,
                        'clients': 0,
                        'revenue': 0
                    }
                
                stats = managers_stats[manager]
                stats['leads'] += 1
                
                revenue = float(lead.get('total_revenue', 0) or 0)
                if revenue > 0:
                    stats['clients'] += 1
                    stats['revenue'] += revenue
            
            # Расчет метрик
            managers_analysis = []
            
            for manager, stats in managers_stats.items():
                conversion = calculate_conversion(stats['clients'], stats['leads'])
                avg_check = stats['revenue'] / stats['clients'] if stats['clients'] > 0 else 0
                
                managers_analysis.append({
                    'name': manager,
                    'leads': stats['leads'],
                    'clients': stats['clients'],
                    'conversion': conversion,
                    'revenue': stats['revenue'],
                    'avg_check': avg_check
                })
            
            # Сортировка по выручке
            managers_analysis.sort(key=lambda x: x['revenue'], reverse=True)
            
            return managers_analysis
            
        except Exception as e:
            logger.error(f"Ошибка анализа менеджеров: {e}")
            return []
    
    async def generate_daily_report(self) -> Optional[Dict[str, Any]]:
        """Генерация ежедневного отчета"""
        try:
            # Получение данных за сегодня
            today = datetime.now().strftime('%Y-%m-%d')
            leads_data = self.sheets_service.read_sheet_data(SHEETS_CONFIG['analytics'])
            
            if not leads_data:
                return None
            
            # Фильтрация лидов за сегодня
            today_leads = [lead for lead in leads_data if lead.get('date', '').startswith(today)]
            
            # Базовая статистика
            new_leads = len(today_leads)
            clients = len([lead for lead in today_leads if float(lead.get('total_revenue', 0) or 0) > 0])
            conversion = calculate_conversion(clients, new_leads)
            revenue = sum(float(lead.get('total_revenue', 0) or 0) for lead in today_leads)
            
            # Анализ каналов за сегодня
            channels_today = {}
            for lead in today_leads:
                channel = lead.get('channel', 'Other')
                if channel not in channels_today:
                    channels_today[channel] = {'leads': 0, 'revenue': 0, 'clients': 0}
                
                channels_today[channel]['leads'] += 1
                lead_revenue = float(lead.get('total_revenue', 0) or 0)
                channels_today[channel]['revenue'] += lead_revenue
                if lead_revenue > 0:
                    channels_today[channel]['clients'] += 1
            
            # Расчет ROI для каналов
            top_channels = []
            for channel, stats in channels_today.items():
                cost = CHANNEL_COSTS.get(channel, 0)
                monthly_cost = cost / 30  # Дневная стоимость
                roi = calculate_roi(stats['revenue'], monthly_cost)
                
                top_channels.append({
                    'name': channel,
                    'revenue': stats['revenue'],
                    'roi': roi,
                    'leads': stats['leads'],
                    'clients': stats['clients']
                })
            
            top_channels.sort(key=lambda x: x['revenue'], reverse=True)
            
            # Общий ROI
            total_cost = sum(CHANNEL_COSTS.values()) / 30  # Дневная стоимость всех каналов
            total_roi = calculate_roi(revenue, total_cost)
            
            # Проверка предупреждений
            alerts = await self._check_daily_alerts(today_leads, channels_today)
            
            return {
                'date': today,
                'new_leads': new_leads,
                'conversion': conversion,
                'revenue': revenue,
                'roi': total_roi,
                'top_channels': top_channels,
                'alerts': alerts
            }
            
        except Exception as e:
            logger.error(f"Ошибка генерации ежедневного отчета: {e}")
            return None
    
    async def _check_daily_alerts(self, today_leads: List[Dict[str, Any]], 
                                channels_today: Dict[str, Any]) -> List[str]:
        """Проверка условий для ежедневных предупреждений"""
        alerts = []
        
        try:
            # Новые VIP клиенты
            new_vip = len([lead for lead in today_leads if lead.get('segment') == 'VIP'])
            if new_vip > 0:
                alerts.append(f"{new_vip} новых VIP клиента")
            
            # Анализ снижения конверсии по каналам
            for channel, stats in channels_today.items():
                if stats['leads'] >= 5:  # Анализируем только каналы с достаточным количеством лидов
                    conversion = calculate_conversion(stats['clients'], stats['leads'])
                    if conversion < 0.1:  # Конверсия ниже 10%
                        alerts.append(f"Низкая конверсия {channel}: {conversion:.1%}")
            
            # Критический ROI каналов
            for channel, stats in channels_today.items():
                cost = CHANNEL_COSTS.get(channel, 0) / 30
                roi = calculate_roi(stats['revenue'], cost)
                if roi < -50 and cost > 100:  # ROI ниже -50% для дорогих каналов
                    alerts.append(f"Критический ROI {channel}: {roi:.1%}")
            
        except Exception as e:
            logger.error(f"Ошибка проверки предупреждений: {e}")
        
        return alerts
    
    async def generate_weekly_report(self) -> Optional[Dict[str, Any]]:
        """Генерация еженедельного отчета"""
        try:
            # Даты для анализа
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            prev_start_date = start_date - timedelta(days=7)
            
            period = f"{start_date.strftime('%d.%m')} - {end_date.strftime('%d.%m.%Y')}"
            
            leads_data = self.sheets_service.read_sheet_data(SHEETS_CONFIG['analytics'])
            
            # Фильтрация данных по периодам
            current_week = self._filter_leads_by_period(leads_data, start_date, end_date)
            previous_week = self._filter_leads_by_period(leads_data, prev_start_date, start_date)
            
            # Расчет метрик
            current_stats = self._calculate_period_stats(current_week)
            previous_stats = self._calculate_period_stats(previous_week)
            
            # Расчет изменений
            leads_change = self._calculate_change(current_stats['leads'], previous_stats['leads'])
            clients_change = self._calculate_change(current_stats['clients'], previous_stats['clients'])
            revenue_change = self._calculate_change(current_stats['revenue'], previous_stats['revenue'])
            
            # Лучший канал недели
            channels_analysis = await self.analyze_channels()
            best_channel = channels_analysis[0]['name'] if channels_analysis else 'Нет данных'
            
            # Новые VIP клиенты
            new_vip = len([lead for lead in current_week if lead.get('segment') == 'VIP'])
            
            # Цели на следующую неделю
            conversion_target = current_stats['conversion'] * 1.1  # +10%
            revenue_target = current_stats['revenue'] * 1.15  # +15%
            
            return {
                'period': period,
                'leads': current_stats['leads'],
                'clients': current_stats['clients'],
                'revenue': current_stats['revenue'],
                'conversion': current_stats['conversion'],
                'leads_change': leads_change,
                'clients_change': clients_change,
                'revenue_change': revenue_change,
                'best_channel': best_channel,
                'new_vip': new_vip,
                'conversion_target': conversion_target,
                'revenue_target': revenue_target
            }
            
        except Exception as e:
            logger.error(f"Ошибка генерации еженедельного отчета: {e}")
            return None
    
    async def generate_monthly_report(self) -> Optional[Dict[str, Any]]:
        """Генерация ежемесячного отчета"""
        try:
            # Прошлый месяц
            today = datetime.now()
            first_day_current = today.replace(day=1)
            last_day_previous = first_day_current - timedelta(days=1)
            first_day_previous = last_day_previous.replace(day=1)
            
            month_name = last_day_previous.strftime('%B %Y')
            
            leads_data = self.sheets_service.read_sheet_data(SHEETS_CONFIG['analytics'])
            
            # Фильтрация данных за прошлый месяц
            month_leads = self._filter_leads_by_period(leads_data, first_day_previous, last_day_previous)
            
            # Основная статистика
            total_revenue = sum(float(lead.get('total_revenue', 0) or 0) for lead in month_leads)
            marketing_costs = sum(CHANNEL_COSTS.values())
            profit = total_revenue - marketing_costs
            roi = calculate_roi(total_revenue, marketing_costs)
            
            # Клиентские показатели
            new_clients = len([lead for lead in month_leads if lead.get('status') == 'Новый'])
            returning_clients = len([lead for lead in month_leads if lead.get('status') == 'Повторный'])
            vip_clients = len([lead for lead in month_leads if lead.get('segment') == 'VIP'])
            
            # Средний LTV
            clients_with_revenue = [lead for lead in month_leads if float(lead.get('total_revenue', 0) or 0) > 0]
            avg_ltv = sum(float(lead.get('ltv', 0) or 0) for lead in clients_with_revenue) / len(clients_with_revenue) if clients_with_revenue else 0
            
            # Топ каналы
            channels_analysis = await self.analyze_channels()
            top_channels = channels_analysis[:5]
            
            return {
                'month': month_name,
                'total_revenue': total_revenue,
                'marketing_costs': marketing_costs,
                'profit': profit,
                'roi': roi,
                'new_clients': new_clients,
                'returning_clients': returning_clients,
                'vip_clients': vip_clients,
                'avg_ltv': avg_ltv,
                'top_channels': top_channels
            }
            
        except Exception as e:
            logger.error(f"Ошибка генерации ежемесячного отчета: {e}")
            return None
    
    async def generate_forecast(self) -> Optional[Dict[str, Any]]:
        """Генерация прогноза выручки на 3 месяца"""
        try:
            leads_data = self.sheets_service.read_sheet_data(SHEETS_CONFIG['analytics'])
            
            if not leads_data:
                return None
            
            # Анализ трендов за последние 3 месяца
            end_date = datetime.now()
            monthly_revenues = []
            
            for i in range(3):
                month_start = (end_date - timedelta(days=30 * (i + 1))).replace(day=1)
                month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                
                month_leads = self._filter_leads_by_period(leads_data, month_start, month_end)
                month_revenue = sum(float(lead.get('total_revenue', 0) or 0) for lead in month_leads)
                monthly_revenues.append(month_revenue)
            
            monthly_revenues.reverse()  # От старого к новому
            
            # Простой линейный тренд
            if len(monthly_revenues) >= 2:
                growth_rate = (monthly_revenues[-1] - monthly_revenues[0]) / len(monthly_revenues) if monthly_revenues[0] > 0 else 0
            else:
                growth_rate = 0
            
            current_revenue = monthly_revenues[-1] if monthly_revenues else 0
            
            # Прогноз на 3 месяца
            forecasts = []
            for i in range(1, 4):
                forecast_revenue = current_revenue + (growth_rate * i)
                forecast_growth = (forecast_revenue - current_revenue) / current_revenue if current_revenue > 0 else 0
                forecasts.append({
                    'month': i,
                    'revenue': max(0, forecast_revenue),  # Не может быть отрицательной
                    'growth': forecast_growth
                })
            
            return {
                'month_1': forecasts[0]['revenue'],
                'growth_1': forecasts[0]['growth'],
                'month_2': forecasts[1]['revenue'],
                'growth_2': forecasts[1]['growth'],
                'month_3': forecasts[2]['revenue'],
                'growth_3': forecasts[2]['growth']
            }
            
        except Exception as e:
            logger.error(f"Ошибка генерации прогноза: {e}")
            return None
    
    async def check_alerts(self) -> List[Dict[str, Any]]:
        """Проверка условий для автоматических уведомлений"""
        alerts = []
        
        try:
            leads_data = self.sheets_service.read_sheet_data(SHEETS_CONFIG['analytics'])
            
            # Проверка новых VIP клиентов за последний час
            hour_ago = datetime.now() - timedelta(hours=1)
            recent_leads = [
                lead for lead in leads_data 
                if self._is_recent_lead(lead.get('date', ''), hour_ago) and lead.get('segment') == 'VIP'
            ]
            
            for lead in recent_leads:
                alerts.append({
                    'type': 'new_vip',
                    'client_name': lead.get('name', 'Неизвестно'),
                    'channel': lead.get('channel', 'Неизвестно'),
                    'revenue': float(lead.get('total_revenue', 0) or 0),
                    'visits': int(lead.get('visits_count', 0) or 0)
                })
            
            # Проверка критического ROI каналов
            channels_analysis = await self.analyze_channels()
            
            for channel in channels_analysis:
                if channel['roi'] < ALERTS_CONFIG.get('roi_threshold', -50) and channel['leads'] >= 10:
                    alerts.append({
                        'type': 'roi_critical',
                        'channel': channel['name'],
                        'roi': channel['roi']
                    })
                
                # Проверка снижения конверсии
                if channel['conversion'] < 0.1 and channel['leads'] >= 20:  # Конверсия ниже 10%
                    alerts.append({
                        'type': 'conversion_drop',
                        'channel': channel['name'],
                        'current_conversion': channel['conversion'],
                        'drop_percentage': 0.25  # Для примера
                    })
            
        except Exception as e:
            logger.error(f"Ошибка проверки уведомлений: {e}")
        
        return alerts
    
    async def update_all_dashboards(self) -> bool:
        """Обновление всех дашбордов в Google Sheets"""
        try:
            logger.info("Начинаю обновление дашбордов")
            
            # Главный дашборд
            await self._update_main_dashboard()
            
            # Анализ каналов
            await self._update_channels_dashboard()
            
            # Сегменты
            await self._update_segments_dashboard()
            
            # Яндекс.Метрика
            await self._update_metrika_dashboard()
            
            # Менеджеры (если есть данные)
            managers_data = await self.analyze_managers()
            if managers_data:
                await self._update_managers_dashboard()
            
            logger.info("Все дашборды обновлены")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка обновления дашбордов: {e}")
            return False
    
    async def _update_main_dashboard(self):
        """Обновление главного дашборда"""
        # Здесь будет логика создания главного дашборда
        # Пока заглушка
        pass
    
    async def _update_channels_dashboard(self):
        """Обновление дашборда каналов"""
        channels_data = await self.analyze_channels()
        
        # Формирование данных для таблицы
        table_data = []
        headers = ['Канал', 'Лиды', 'Клиенты', 'Конверсия', 'Выручка', 'CAC', 'LTV', 'ROI', 'Рейтинг']
        
        for channel in channels_data:
            row = [
                channel['name'],
                channel['leads'],
                channel['clients'],
                f"{channel['conversion']:.1%}",
                f"{channel['revenue']:,.0f} ₽",
                f"{channel['cac']:,.0f} ₽",
                f"{channel['ltv']:,.0f} ₽",
                f"{channel['roi']:.1%}",
                "★" * int(channel['rating'])
            ]
            table_data.append(row)
        
        dashboard_data = {
            'title': f'{EMOJI["chart_up"]} Анализ Каналов - {datetime.now().strftime("%d.%m.%Y")}',
            'tables': [{
                'table_title': 'Эффективность каналов привлечения',
                'headers': headers,
                'data': table_data
            }],
            'roi_column': 'H'  # Колонка ROI для условного форматирования
        }
        
        self.sheets_service.create_dashboard(SHEETS_CONFIG['channels_analysis'], dashboard_data)
    
    async def _update_segments_dashboard(self):
        """Обновление дашборда сегментов"""
        segments_data = await self.analyze_segments()
        
        # Формирование данных для таблицы
        table_data = []
        headers = ['Сегмент', 'Количество', 'Доля', 'Выручка', 'Доля выручки', 'Средний чек', 'Среднее визитов']
        
        total_clients = sum(segment['count'] for segment in segments_data)
        total_revenue = sum(segment['revenue'] for segment in segments_data)
        
        for segment in segments_data:
            client_share = segment['count'] / total_clients if total_clients > 0 else 0
            revenue_share = segment['revenue'] / total_revenue if total_revenue > 0 else 0
            
            row = [
                f"{segment['emoji']} {segment['name']}",
                segment['count'],
                f"{client_share:.1%}",
                f"{segment['revenue']:,.0f} ₽",
                f"{revenue_share:.1%}",
                f"{segment['avg_check']:,.0f} ₽",
                f"{segment['avg_visits']:.1f}"
            ]
            table_data.append(row)
        
        # Итоговая строка
        table_data.append([
            'ИТОГО',
            total_clients,
            '100%',
            f"{total_revenue:,.0f} ₽",
            '100%',
            f"{total_revenue / total_clients if total_clients > 0 else 0:,.0f} ₽",
            f"{sum(segment['avg_visits'] * segment['count'] for segment in segments_data) / total_clients if total_clients > 0 else 0:.1f}"
        ])
        
        dashboard_data = {
            'title': f'{EMOJI["users"]} Сегментация Клиентов - {datetime.now().strftime("%d.%m.%Y")}',
            'tables': [{
                'table_title': 'Распределение клиентов по сегментам',
                'headers': headers,
                'data': table_data
            }]
        }
        
        self.sheets_service.create_dashboard(SHEETS_CONFIG['segments_analysis'], dashboard_data)
    
    async def _update_metrika_dashboard(self):
        """Обновление дашборда Яндекс.Метрики"""
        # Получение данных по каналам из Метрики
        channels_analysis = await self.analyze_channels()
        
        table_data = []
        headers = ['Канал', 'Визиты', 'Просмотры', 'Отказы', 'Время на сайте', 'Индекс вовлеченности']
        
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        for channel in channels_analysis[:10]:  # Топ 10 каналов
            metrika_data = await self.metrika_service.get_channel_metrics(channel['name'], start_date, end_date)
            
            engagement_stars = "★" * max(1, min(5, int(metrika_data.get('engagement_rate', 0) / 20)))
            
            row = [
                channel['name'],
                metrika_data.get('visits', 0),
                metrika_data.get('pageviews', 0),
                f"{metrika_data.get('bounce_rate', 0):.1f}%",
                f"{metrika_data.get('avg_visit_duration', 0)}с",
                f"{engagement_stars} ({metrika_data.get('engagement_rate', 0):.1f})"
            ]
            table_data.append(row)
        
        dashboard_data = {
            'title': f'{EMOJI["chart_up"]} Яндекс.Метрика - {datetime.now().strftime("%d.%m.%Y")}',
            'tables': [{
                'table_title': 'Показатели вовлеченности по каналам (30 дней)',
                'headers': headers,
                'data': table_data
            }]
        }
        
        self.sheets_service.create_dashboard(SHEETS_CONFIG['metrika_analysis'], dashboard_data)
    
    async def _update_managers_dashboard(self):
        """Обновление дашборда менеджеров"""
        managers_data = await self.analyze_managers()
        
        if not managers_data:
            return
        
        table_data = []
        headers = ['Менеджер', 'Лиды', 'Клиенты', 'Конверсия', 'Выручка', 'Средний чек']
        
        for manager in managers_data:
            row = [
                manager['name'],
                manager['leads'],
                manager['clients'],
                f"{manager['conversion']:.1%}",
                f"{manager['revenue']:,.0f} ₽",
                f"{manager['avg_check']:,.0f} ₽"
            ]
            table_data.append(row)
        
        dashboard_data = {
            'title': f'{EMOJI["users"]} Эффективность Менеджеров - {datetime.now().strftime("%d.%m.%Y")}',
            'tables': [{
                'table_title': 'Показатели работы менеджеров',
                'headers': headers,
                'data': table_data
            }]
        }
        
        self.sheets_service.create_dashboard(SHEETS_CONFIG['managers_analysis'], dashboard_data)
    
    def _filter_leads_by_period(self, leads: List[Dict[str, Any]], 
                               start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Фильтрация лидов по периоду"""
        filtered_leads = []
        
        for lead in leads:
            lead_date_str = lead.get('date', '')
            if lead_date_str:
                try:
                    lead_date = datetime.strptime(lead_date_str.split(' ')[0], '%Y-%m-%d')
                    if start_date <= lead_date <= end_date:
                        filtered_leads.append(lead)
                except ValueError:
                    continue
        
        return filtered_leads
    
    def _calculate_period_stats(self, leads: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Расчет статистики за период"""
        total_leads = len(leads)
        clients = len([lead for lead in leads if float(lead.get('total_revenue', 0) or 0) > 0])
        revenue = sum(float(lead.get('total_revenue', 0) or 0) for lead in leads)
        conversion = calculate_conversion(clients, total_leads)
        
        return {
            'leads': total_leads,
            'clients': clients,
            'revenue': revenue,
            'conversion': conversion
        }
    
    def _calculate_change(self, current: float, previous: float) -> float:
        """Расчет изменения в процентах"""
        if previous == 0:
            return 0 if current == 0 else 100
        return (current - previous) / previous
    
    def _is_recent_lead(self, date_str: str, threshold: datetime) -> bool:
        """Проверка, является ли лид недавним"""
        if not date_str:
            return False
        
        try:
            lead_date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
            return lead_date >= threshold
        except ValueError:
            return False
