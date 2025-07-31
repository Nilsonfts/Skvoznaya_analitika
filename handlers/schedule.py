"""
Планировщик задач для автоматических операций
"""

import asyncio
import logging
from datetime import datetime, time
from typing import Dict, Any

from telegram.ext import Application
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from config import ADMIN_IDS, ALERTS_CONFIG, EMOJI
from services.analytics import AnalyticsService
from utils.formatters import format_currency, format_percentage

logger = logging.getLogger(__name__)

class SchedulerService:
    def __init__(self, application: Application):
        self.application = application
        self.scheduler = AsyncIOScheduler()
        self.analytics = AnalyticsService()
        
    async def hourly_update(self):
        """Ежечасное обновление лидов"""
        try:
            logger.info("Выполняю ежечасное обновление лидов")
            result = await self.analytics.merge_all_leads()
            
            if result['success'] and result['new_leads'] > 0:
                # Уведомление администраторов о новых лидах
                message = f"""
{EMOJI['new']} **НОВЫЕ ЛИДЫ**

Добавлено лидов: {result['new_leads']}
Время: {datetime.now().strftime('%H:%M')}
"""
                await self._send_to_admins(message)
                
        except Exception as e:
            logger.error(f"Error in hourly_update: {e}")
    
    async def daily_report(self):
        """Ежедневный отчёт в 9:00"""
        try:
            logger.info("Формирую ежедневный отчёт")
            
            # Полное обновление данных
            await self.analytics.merge_all_leads()
            await self.analytics.update_all_dashboards()
            
            # Генерация отчёта
            report_data = await self.analytics.generate_daily_report()
            
            if not report_data:
                return
            
            today = datetime.now().strftime("%d.%m.%Y")
            
            report_text = f"""
{EMOJI['report']} **ЕЖЕДНЕВНЫЙ ОТЧЁТ**
Дата: {today}

{EMOJI['users']} Новых лидов: {report_data['new_leads']}
{EMOJI['chart_up']} Конверсия: {format_percentage(report_data['conversion'])}
{EMOJI['money']} Выручка: {format_currency(report_data['revenue'])}
{EMOJI['chart_up']} ROI: {format_percentage(report_data['roi'])}

{EMOJI['top']} **ТОП-3 КАНАЛА:**
"""
            
            for i, channel in enumerate(report_data['top_channels'][:3], 1):
                roi_emoji = EMOJI['chart_up'] if channel['roi'] > 0 else EMOJI['chart_down']
                report_text += f"{i}. {channel['name']}: {format_currency(channel['revenue'])} (ROI: {roi_emoji}{format_percentage(channel['roi'])})\n"
            
            if report_data['alerts']:
                report_text += f"\n{EMOJI['warning']} **Требует внимания:**\n"
                for alert in report_data['alerts']:
                    report_text += f"• {alert}\n"
            
            await self._send_to_admins(report_text)
            
        except Exception as e:
            logger.error(f"Error in daily_report: {e}")
    
    async def weekly_report(self):
        """Еженедельный отчёт по понедельникам"""
        try:
            logger.info("Формирую еженедельный отчёт")
            
            weekly_data = await self.analytics.generate_weekly_report()
            
            if not weekly_data:
                return
            
            report_text = f"""
{EMOJI['calendar']} **ЕЖЕНЕДЕЛЬНЫЙ ОТЧЁТ**
Период: {weekly_data['period']}

{EMOJI['chart_up']} **Основные показатели:**
• Лиды: {weekly_data['leads']} (изменение: {format_percentage(weekly_data['leads_change'])})
• Клиенты: {weekly_data['clients']} (изменение: {format_percentage(weekly_data['clients_change'])})
• Выручка: {format_currency(weekly_data['revenue'])} (изменение: {format_percentage(weekly_data['revenue_change'])})
• Конверсия: {format_percentage(weekly_data['conversion'])}

{EMOJI['top']} **Лучший канал недели:** {weekly_data['best_channel']}
{EMOJI['new']} **Новых VIP клиентов:** {weekly_data['new_vip']}

{EMOJI['fire']} **Цели на следующую неделю:**
• Увеличить конверсию до {format_percentage(weekly_data['conversion_target'])}
• Достичь выручки {format_currency(weekly_data['revenue_target'])}
"""
            
            await self._send_to_admins(report_text)
            
        except Exception as e:
            logger.error(f"Error in weekly_report: {e}")
    
    async def monthly_report(self):
        """Ежемесячный отчёт в первый день месяца"""
        try:
            logger.info("Формирую ежемесячный отчёт")
            
            monthly_data = await self.analytics.generate_monthly_report()
            
            if not monthly_data:
                return
            
            report_text = f"""
{EMOJI['calendar']} **ЕЖЕМЕСЯЧНЫЙ ОТЧЁТ**
Месяц: {monthly_data['month']}

{EMOJI['money']} **Финансовые показатели:**
• Общая выручка: {format_currency(monthly_data['total_revenue'])}
• Расходы на маркетинг: {format_currency(monthly_data['marketing_costs'])}
• Прибыль: {format_currency(monthly_data['profit'])}
• ROI: {format_percentage(monthly_data['roi'])}

{EMOJI['users']} **Клиентские показатели:**
• Новых клиентов: {monthly_data['new_clients']}
• Повторных клиентов: {monthly_data['returning_clients']}
• VIP клиентов: {monthly_data['vip_clients']}
• Средний LTV: {format_currency(monthly_data['avg_ltv'])}

{EMOJI['chart_up']} **Лучшие каналы месяца:**
"""
            
            for i, channel in enumerate(monthly_data['top_channels'][:5], 1):
                report_text += f"{i}. {channel['name']}: ROI {format_percentage(channel['roi'])}\n"
            
            await self._send_to_admins(report_text)
            
        except Exception as e:
            logger.error(f"Error in monthly_report: {e}")
    
    async def check_alerts(self):
        """Проверка условий для автоматических уведомлений"""
        try:
            alerts = await self.analytics.check_alerts()
            
            for alert in alerts:
                if alert['type'] == 'new_vip':
                    message = f"""
{EMOJI['crown']} **НОВЫЙ VIP КЛИЕНТ!**

Клиент: {alert['client_name']}
Канал: {alert['channel']}
Выручка: {format_currency(alert['revenue'])}
Визиты: {alert['visits']}
"""
                    await self._send_to_admins(message)
                
                elif alert['type'] == 'conversion_drop':
                    message = f"""
{EMOJI['warning']} **СНИЖЕНИЕ КОНВЕРСИИ**

Канал: {alert['channel']}
Текущая конверсия: {format_percentage(alert['current_conversion'])}
Снижение: {format_percentage(alert['drop_percentage'])}

Требуется анализ и корректировка стратегии.
"""
                    await self._send_to_admins(message)
                
                elif alert['type'] == 'roi_critical':
                    message = f"""
{EMOJI['chart_down']} **КРИТИЧЕСКИЙ ROI**

Канал: {alert['channel']}
ROI: {format_percentage(alert['roi'])}
Рекомендация: пересмотреть бюджет или стратегию
"""
                    await self._send_to_admins(message)
                
        except Exception as e:
            logger.error(f"Error in check_alerts: {e}")
    
    async def _send_to_admins(self, message: str):
        """Отправка сообщения всем администраторам"""
        for admin_id in ADMIN_IDS:
            try:
                await self.application.bot.send_message(
                    chat_id=admin_id,
                    text=message,
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Failed to send message to admin {admin_id}: {e}")
    
    def start(self):
        """Запуск планировщика"""
        try:
            # Ежечасное обновление лидов
            self.scheduler.add_job(
                self.hourly_update,
                trigger=IntervalTrigger(hours=1),
                id='hourly_update',
                name='Ежечасное обновление лидов'
            )
            
            # Ежедневный отчёт в 9:00 МСК
            self.scheduler.add_job(
                self.daily_report,
                trigger=CronTrigger(hour=9, minute=0, timezone='Europe/Moscow'),
                id='daily_report',
                name='Ежедневный отчёт'
            )
            
            # Еженедельный отчёт по понедельникам в 10:00
            self.scheduler.add_job(
                self.weekly_report,
                trigger=CronTrigger(day_of_week=0, hour=10, minute=0, timezone='Europe/Moscow'),
                id='weekly_report',
                name='Еженедельный отчёт'
            )
            
            # Ежемесячный отчёт в первый день месяца в 11:00
            self.scheduler.add_job(
                self.monthly_report,
                trigger=CronTrigger(day=1, hour=11, minute=0, timezone='Europe/Moscow'),
                id='monthly_report',
                name='Ежемесячный отчёт'
            )
            
            # Проверка уведомлений каждые 15 минут
            self.scheduler.add_job(
                self.check_alerts,
                trigger=IntervalTrigger(minutes=15),
                id='check_alerts',
                name='Проверка уведомлений'
            )
            
            self.scheduler.start()
            logger.info("Планировщик задач запущен")
            
        except Exception as e:
            logger.error(f"Error starting scheduler: {e}")
    
    def stop(self):
        """Остановка планировщика"""
        self.scheduler.shutdown()
        logger.info("Планировщик задач остановлен")

def setup_scheduler(application: Application):
    """Настройка и запуск планировщика"""
    scheduler_service = SchedulerService(application)
    scheduler_service.start()
    
    # Сохраняем ссылку на планировщик в приложении для корректного завершения
    application.bot_data['scheduler'] = scheduler_service
    
    return scheduler_service
