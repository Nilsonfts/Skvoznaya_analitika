"""
Обработчики команд Telegram-бота
"""

import logging
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes

from config import EMOJI, ADMIN_IDS
from services.analytics import AnalyticsService
from utils.formatters import format_number, format_percentage, format_currency

logger = logging.getLogger(__name__)

# Глобальное состояние для уведомлений
alerts_enabled = {}

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /start - приветствие и основная информация"""
    user = update.effective_user
    welcome_text = f"""
{EMOJI['rocket']} Добро пожаловать в аналитический бот "Евгенич СПБ"!

Привет, {user.first_name}! Я помогу вам отслеживать маркетинговые показатели вашего бизнеса.

{EMOJI['info']} **Основные команды:**
• /report - ежедневный отчёт
• /channels - анализ каналов привлечения
• /segments - сегментация клиентов
• /managers - эффективность менеджеров
• /help - подробная справка

{EMOJI['chart_up']} **Что я умею:**
• Собираю лиды из Google Sheets
• Рассчитываю CAC, LTV, ROI
• Интегрируюсь с Яндекс.Метрикой
• Создаю дашборды и отчёты
• Отправляю уведомления по расписанию

Используйте /help для получения полного списка команд.
"""
    
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /help - подробная справка"""
    help_text = f"""
{EMOJI['info']} **Справка по командам бота "Евгенич СПБ"**

{EMOJI['report']} **Отчёты:**
• `/report` - краткий ежедневный отчёт
• `/channels` - анализ всех каналов привлечения
• `/channel <название>` - детальный анализ канала
• `/segments` - сегментация клиентов
• `/managers` - эффективность менеджеров

{EMOJI['chart_up']} **Аналитика:**
• `/forecast` - прогноз выручки (только админы)
• `/test_metrika` - проверка Яндекс.Метрики (только админы)

⚙️ **Управление:**
• `/update` - обновить данные (только админы)
• `/alerts on/off` - управление уведомлениями

{EMOJI['calendar']} **Автоматические функции:**
• Ежечасное обновление данных
• Ежедневный отчёт в 9:00 МСК
• Уведомления о новых VIP-клиентах
• Предупреждения о снижении показателей

{EMOJI['info']} **Метрики:**
• CAC - стоимость привлечения клиента
• LTV - пожизненная ценность клиента
• ROI - возврат инвестиций
• Конверсия - процент лидов в клиенты

Для получения дополнительной помощи обратитесь к администратору.
"""
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /report - краткий ежедневный отчёт"""
    try:
        await update.message.reply_text(f"{EMOJI['clock']} Формирую отчёт...")
        
        analytics = AnalyticsService()
        report_data = await analytics.generate_daily_report()
        
        if not report_data:
            await update.message.reply_text(f"{EMOJI['error']} Не удалось получить данные для отчёта")
            return
        
        # Форматирование отчёта
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
        
        report_text += f"\nПодробнее: /channels"
        
        await update.message.reply_text(report_text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in report_command: {e}")
        await update.message.reply_text(f"{EMOJI['error']} Ошибка при формировании отчёта")

async def channels_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /channels - анализ всех каналов"""
    try:
        await update.message.reply_text(f"{EMOJI['clock']} Анализирую каналы...")
        
        analytics = AnalyticsService()
        channels_data = await analytics.analyze_channels()
        
        if not channels_data:
            await update.message.reply_text(f"{EMOJI['error']} Не удалось получить данные по каналам")
            return
        
        report_text = f"{EMOJI['chart_up']} **АНАЛИЗ КАНАЛОВ ПРИВЛЕЧЕНИЯ**\n\n"
        
        for channel in channels_data:
            roi_stars = "★" * max(1, min(5, int(channel['rating'])))
            roi_emoji = EMOJI['chart_up'] if channel['roi'] > 0 else EMOJI['chart_down']
            
            report_text += f"**{channel['name']}** {roi_stars}\n"
            report_text += f"• Лиды: {channel['leads']} | Клиенты: {channel['clients']}\n"
            report_text += f"• Конверсия: {format_percentage(channel['conversion'])}\n"
            report_text += f"• Выручка: {format_currency(channel['revenue'])}\n"
            report_text += f"• CAC: {format_currency(channel['cac'])} | LTV: {format_currency(channel['ltv'])}\n"
            report_text += f"• ROI: {roi_emoji}{format_percentage(channel['roi'])}\n\n"
        
        report_text += f"Детальный анализ: `/channel <название>`"
        
        await update.message.reply_text(report_text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in channels_command: {e}")
        await update.message.reply_text(f"{EMOJI['error']} Ошибка при анализе каналов")

async def channel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /channel <название> - детальный анализ канала"""
    if not context.args:
        await update.message.reply_text("Укажите название канала. Пример: `/channel Yandex`", parse_mode='Markdown')
        return
    
    channel_name = ' '.join(context.args)
    
    try:
        analytics = AnalyticsService()
        channel_data = await analytics.analyze_channel(channel_name)
        
        if not channel_data:
            await update.message.reply_text(f"{EMOJI['error']} Канал '{channel_name}' не найден")
            return
        
        roi_emoji = EMOJI['chart_up'] if channel_data['roi'] > 0 else EMOJI['chart_down']
        rating_stars = "★" * max(1, min(5, int(channel_data['rating'])))
        
        report_text = f"""
{EMOJI['chart_up']} **ДЕТАЛЬНЫЙ АНАЛИЗ КАНАЛА: {channel_name}**

{EMOJI['star']} Рейтинг: {rating_stars} ({channel_data['rating']:.1f}/5)

{EMOJI['users']} **Основные показатели:**
• Всего лидов: {channel_data['total_leads']}
• Клиенты: {channel_data['clients']} ({format_percentage(channel_data['conversion'])})
• Новые клиенты: {channel_data['new_clients']}
• VIP клиенты: {channel_data['vip_clients']}

{EMOJI['money']} **Финансовые показатели:**
• Общая выручка: {format_currency(channel_data['revenue'])}
• Средний чек: {format_currency(channel_data['avg_check'])}
• CAC: {format_currency(channel_data['cac'])}
• LTV: {format_currency(channel_data['ltv'])}
• ROI: {roi_emoji}{format_percentage(channel_data['roi'])}

{EMOJI['calendar']} **Временные показатели:**
• Период окупаемости: {channel_data['payback_visits']} визитов
• Последняя активность: {channel_data['last_activity']}
"""
        
        if channel_data['metrika_data']:
            metrika = channel_data['metrika_data']
            report_text += f"""
{EMOJI['chart_up']} **Яндекс.Метрика:**
• Визиты: {metrika['visits']}
• Просмотры: {metrika['pageviews']}
• Отказы: {format_percentage(metrika['bounce_rate'])}
• Время на сайте: {metrika['avg_duration']}с
"""
        
        await update.message.reply_text(report_text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in channel_command: {e}")
        await update.message.reply_text(f"{EMOJI['error']} Ошибка при анализе канала")

async def segments_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /segments - сегментация клиентов"""
    try:
        await update.message.reply_text(f"{EMOJI['clock']} Анализирую сегменты...")
        
        analytics = AnalyticsService()
        segments_data = await analytics.analyze_segments()
        
        if not segments_data:
            await update.message.reply_text(f"{EMOJI['error']} Не удалось получить данные по сегментам")
            return
        
        report_text = f"{EMOJI['users']} **СЕГМЕНТАЦИЯ КЛИЕНТОВ**\n\n"
        
        total_clients = sum(segment['count'] for segment in segments_data)
        total_revenue = sum(segment['revenue'] for segment in segments_data)
        
        for segment in segments_data:
            emoji = segment['emoji']
            percentage = (segment['count'] / total_clients * 100) if total_clients > 0 else 0
            revenue_share = (segment['revenue'] / total_revenue * 100) if total_revenue > 0 else 0
            
            report_text += f"{emoji} **{segment['name']}** ({format_percentage(percentage/100)})\n"
            report_text += f"• Клиенты: {segment['count']}\n"
            report_text += f"• Выручка: {format_currency(segment['revenue'])} ({format_percentage(revenue_share/100)})\n"
            report_text += f"• Средний чек: {format_currency(segment['avg_check'])}\n"
            report_text += f"• Среднее визитов: {segment['avg_visits']:.1f}\n\n"
        
        report_text += f"**ИТОГО:**\n"
        report_text += f"• Всего клиентов: {total_clients}\n"
        report_text += f"• Общая выручка: {format_currency(total_revenue)}"
        
        await update.message.reply_text(report_text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in segments_command: {e}")
        await update.message.reply_text(f"{EMOJI['error']} Ошибка при анализе сегментов")

async def managers_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /managers - эффективность менеджеров"""
    try:
        await update.message.reply_text(f"{EMOJI['clock']} Анализирую работу менеджеров...")
        
        analytics = AnalyticsService()
        managers_data = await analytics.analyze_managers()
        
        if not managers_data:
            await update.message.reply_text(f"{EMOJI['info']} Данные по менеджерам отсутствуют")
            return
        
        report_text = f"{EMOJI['users']} **ЭФФЕКТИВНОСТЬ МЕНЕДЖЕРОВ**\n\n"
        
        for manager in managers_data:
            report_text += f"**{manager['name']}**\n"
            report_text += f"• Лиды: {manager['leads']} | Клиенты: {manager['clients']}\n"
            report_text += f"• Конверсия: {format_percentage(manager['conversion'])}\n"
            report_text += f"• Выручка: {format_currency(manager['revenue'])}\n"
            report_text += f"• Средний чек: {format_currency(manager['avg_check'])}\n\n"
        
        await update.message.reply_text(report_text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in managers_command: {e}")
        await update.message.reply_text(f"{EMOJI['error']} Ошибка при анализе менеджеров")

async def update_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /update - принудительное обновление данных (только админы)"""
    try:
        await update.message.reply_text(f"{EMOJI['clock']} Обновляю данные...")
        
        analytics = AnalyticsService()
        result = await analytics.merge_all_leads()
        
        if result['success']:
            report_text = f"""
{EMOJI['success']} **ДАННЫЕ ОБНОВЛЕНЫ**

• Обработано лидов с сайта: {result['site_leads']}
• Обработано лидов из соцсетей: {result['social_leads']}
• Новых лидов добавлено: {result['new_leads']}
• Дубликатов пропущено: {result['duplicates']}
• Обогащено данными клиентов: {result['enriched']}

Время обновления: {datetime.now().strftime('%H:%M:%S')}
"""
        else:
            report_text = f"{EMOJI['error']} Ошибка при обновлении: {result['error']}"
        
        await update.message.reply_text(report_text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in update_command: {e}")
        await update.message.reply_text(f"{EMOJI['error']} Ошибка при обновлении данных")

async def forecast_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /forecast - прогноз выручки (только админы)"""
    try:
        await update.message.reply_text(f"{EMOJI['clock']} Строю прогноз...")
        
        analytics = AnalyticsService()
        forecast_data = await analytics.generate_forecast()
        
        if not forecast_data:
            await update.message.reply_text(f"{EMOJI['error']} Не удалось построить прогноз")
            return
        
        report_text = f"""
{EMOJI['chart_up']} **ПРОГНОЗ ВЫРУЧКИ НА 3 МЕСЯЦА**

{EMOJI['calendar']} **Следующий месяц:**
• Прогнозируемая выручка: {format_currency(forecast_data['month_1'])}
• Рост к текущему месяцу: {format_percentage(forecast_data['growth_1'])}

{EMOJI['calendar']} **Через 2 месяца:**
• Прогнозируемая выручка: {format_currency(forecast_data['month_2'])}
• Рост к текущему месяцу: {format_percentage(forecast_data['growth_2'])}

{EMOJI['calendar']} **Через 3 месяца:**
• Прогнозируемая выручка: {format_currency(forecast_data['month_3'])}
• Рост к текущему месяцу: {format_percentage(forecast_data['growth_3'])}

{EMOJI['info']} Прогноз основан на текущих трендах и исторических данных.
"""
        
        await update.message.reply_text(report_text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in forecast_command: {e}")
        await update.message.reply_text(f"{EMOJI['error']} Ошибка при построении прогноза")

async def alerts_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /alerts on/off - управление уведомлениями"""
    global alerts_enabled
    
    user_id = update.effective_user.id
    
    if not context.args or context.args[0].lower() not in ['on', 'off']:
        status = "включены" if alerts_enabled.get(user_id, True) else "выключены"
        await update.message.reply_text(f"Уведомления сейчас {status}. Используйте `/alerts on` или `/alerts off`", parse_mode='Markdown')
        return
    
    action = context.args[0].lower()
    
    if action == 'on':
        alerts_enabled[user_id] = True
        await update.message.reply_text(f"{EMOJI['success']} Уведомления включены")
    else:
        alerts_enabled[user_id] = False
        await update.message.reply_text(f"{EMOJI['info']} Уведомления выключены")

async def test_metrika_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /test_metrika - проверка соединения с Яндекс.Метрикой (только админы)"""
    try:
        await update.message.reply_text(f"{EMOJI['clock']} Проверяю соединение с Яндекс.Метрикой...")
        
        from services.metrika import MetrikaService
        metrika = MetrikaService()
        
        test_result = await metrika.test_connection()
        
        if test_result['success']:
            report_text = f"""
{EMOJI['success']} **СОЕДИНЕНИЕ С ЯНДЕКС.МЕТРИКОЙ УСПЕШНО**

• Счётчик: {test_result['counter_id']}
• Визиты за вчера: {test_result['yesterday_visits']}
• Статус API: Активен
• Время ответа: {test_result['response_time']}мс
"""
        else:
            report_text = f"{EMOJI['error']} **ОШИБКА СОЕДИНЕНИЯ**\n\n{test_result['error']}"
        
        await update.message.reply_text(report_text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in test_metrika_command: {e}")
        await update.message.reply_text(f"{EMOJI['error']} Ошибка при проверке Яндекс.Метрики")
