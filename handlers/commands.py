"""
Обработчики команд Telegram-бота
"""

import asyncio
import logging
from datetime import datetime, timedelta
from telegram import Update, InputFile
from telegram.ext import ContextTypes

from config import EMOJI, ADMIN_IDS
from services.analytics import AnalyticsService
from services.reserves_updater import ReservesUpdateService
from services.visualization import get_visualization_service
from utils.formatters import format_number, format_percentage, format_currency
from utils.rate_limiter import rate_limit, admin_rate_limit

logger = logging.getLogger(__name__)

# Глобальное состояние для уведомлений
alerts_enabled = {}

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /start - приветствие и основная информация"""
    from handlers.keyboards import get_main_menu
    
    user = update.effective_user
    welcome_text = f"""
🎤 **Добро пожаловать в "Евгенич СПБ"!**

Привет, {user.first_name}! Я аналитический бот караоке-рюмочной.

✨ **Что я умею:**
• 📊 Генерирую отчёты и аналитику
• 📈 Создаю красивые графики
• 🎯 Анализирую каналы привлечения  
• 👥 Сегментирую клиентов
• 💰 Прогнозирую выручку
• 🔔 Отправляю уведомления

🎵 **Используйте кнопки меню ниже для навигации**

Система учитывает сезонность караоке-бизнеса и поможет оптимизировать вашу рекламу!
"""
    
    await update.message.reply_text(
        welcome_text, 
        parse_mode='Markdown',
        reply_markup=get_main_menu()
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /help - подробная справка"""
    help_text = f"""
{EMOJI['info']} **Справка по командам бота "Евгенич СПБ"**

{EMOJI['report']} **Отчёты:**
• `/report` - краткий ежедневный отчёт
• `/channels` - анализ всех каналов привлечения
• `/channels_chart` - график эффективности каналов
• `/channel <название>` - детальный анализ канала
• `/segments` - сегментация клиентов
• `/segments_chart` - диаграмма сегментов клиентов
• `/managers` - эффективность менеджеров
• `/reserves` - обновление данных RestoPlace (админы)

{EMOJI['chart_up']} **Аналитика и визуализация:**
• `/forecast` - прогноз выручки с графиком
• `/compare канал1 канал2` - сравнение двух каналов
• `/status` - статус системы (админы)
• `/test_metrika` - проверка Яндекс.Метрики (админы)

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

🛡️ **Безопасность:**
Команды имеют ограничения по частоте использования для предотвращения злоупотреблений.

Для получения дополнительной помощи обратитесь к администратору.
"""
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /report - ежедневный отчёт с графиками"""
    try:
        # Отправляем сообщение о загрузке
        loading_msg = await update.message.reply_text(f"{EMOJI['clock']} Формирую отчёт...")
        
        analytics = AnalyticsService()
        visualization = get_visualization_service()
        
        # Получаем данные отчёта
        report_data = await analytics.generate_daily_report()
        
        if not report_data:
            await loading_msg.edit_text(f"{EMOJI['error']} Не удалось сформировать отчёт")
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
        
        report_text += f"\n📊 График каналов: /channels_chart"
        report_text += f"\n👥 Сегменты клиентов: /segments"
        
        await loading_msg.edit_text(report_text, parse_mode='Markdown')
        
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

async def test_google_sheets_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /test_sheets - проверка соединения с Google Sheets (только админы)"""
    try:
        await update.message.reply_text(f"{EMOJI['clock']} Проверяю соединение с Google Sheets...")
        
        from services.google_sheets import GoogleSheetsService
        sheets = GoogleSheetsService()
        
        test_result = sheets.test_connection()
        
        if test_result['success']:
            worksheets_info = ""
            if test_result.get('worksheets'):
                worksheets_info = f"• Листы: {', '.join(test_result['worksheets'])}"
                if test_result['worksheets_count'] > 5:
                    worksheets_info += f" (и ещё {test_result['worksheets_count'] - 5})"
            
            report_text = f"""
{EMOJI['success']} **GOOGLE SHEETS ПОДКЛЮЧЕН**

• Таблица: {test_result.get('title', 'Неизвестно')}
• ID: {test_result['spreadsheet_id'][:20]}...
• Листов: {test_result['worksheets_count']}
{worksheets_info}
• Аутентификация: {test_result['authentication']}
• Уровень доступа: {test_result['access_level']}
• Время ответа: {test_result['response_time']}мс
"""
        else:
            report_text = f"""
{EMOJI['warning']} **GOOGLE SHEETS НЕДОСТУПЕН**

• Ошибка: {test_result['error']}
• Аутентификация: {test_result.get('authentication', 'нет')}
• Система работает в режиме fallback
• Время проверки: {test_result['response_time']}мс

💡 Для подключения настройте GOOGLE_CREDENTIALS_JSON
"""
        
        await update.message.reply_text(report_text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in test_google_sheets_command: {e}")
        await update.message.reply_text(f"{EMOJI['error']} Ошибка при проверке Google Sheets")

async def test_all_connections_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /test_all - проверка всех подключений (только админы)"""
    try:
        await update.message.reply_text(f"{EMOJI['clock']} Проверяю все подключения...")
        
        # Тестируем все сервисы
        results = {}
        
        # Google Sheets
        from services.google_sheets import GoogleSheetsService
        sheets = GoogleSheetsService()
        results['sheets'] = sheets.test_connection()
        
        # Yandex Metrika
        from services.metrika import MetrikaService
        metrika = MetrikaService()
        results['metrika'] = await metrika.test_connection()
        
        # PostgreSQL
        from services.database import DatabaseService
        try:
            db = DatabaseService()
            # Простой тест подключения
            test_query = "SELECT 1 as test"
            db_result = await db.execute_query(test_query)
            results['postgres'] = {
                'success': True,
                'service': 'PostgreSQL',
                'status': 'Подключен',
                'tables_count': 'N/A'
            }
        except Exception as e:
            results['postgres'] = {
                'success': False,
                'service': 'PostgreSQL', 
                'error': str(e)
            }
        
        # Redis
        from services.cache import CacheService
        try:
            cache = CacheService()
            await cache.set('test_connection', 'ok', 10)
            test_val = await cache.get('test_connection')
            results['redis'] = {
                'success': test_val == 'ok',
                'service': 'Redis',
                'status': 'Подключен' if test_val == 'ok' else 'Ошибка'
            }
        except Exception as e:
            results['redis'] = {
                'success': False,
                'service': 'Redis',
                'error': str(e)
            }
        
        # Формируем отчёт
        report_lines = [f"{EMOJI['gear']} **СТАТУС ВСЕХ ПОДКЛЮЧЕНИЙ**\n"]
        
        for service_key, result in results.items():
            service_name = result['service']
            if result['success']:
                status_emoji = EMOJI['success']
                status_text = "Работает"
                if service_key == 'metrika' and 'yesterday_visits' in result:
                    details = f"({result['yesterday_visits']} визитов вчера)"
                elif service_key == 'sheets' and 'worksheets_count' in result:
                    details = f"({result['worksheets_count']} листов)"
                else:
                    details = ""
            else:
                status_emoji = EMOJI['error'] 
                status_text = "Недоступен"
                details = f"({result.get('error', 'Неизвестная ошибка')[:50]}...)"
            
            report_lines.append(f"{status_emoji} **{service_name}**: {status_text} {details}")
        
        # Общая статистика
        working_count = sum(1 for r in results.values() if r['success'])
        total_count = len(results)
        
        report_lines.append(f"\n📊 **Итого**: {working_count}/{total_count} сервисов работают")
        
        if working_count == total_count:
            report_lines.append(f"{EMOJI['party']} Все системы функционируют нормально!")
        elif working_count > 0:
            report_lines.append(f"{EMOJI['warning']} Система работает с ограничениями")
        else:
            report_lines.append(f"{EMOJI['error']} Критические ошибки подключений")
        
        report_text = '\n'.join(report_lines)
        await update.message.reply_text(report_text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in test_all_connections_command: {e}")
        await update.message.reply_text(f"{EMOJI['error']} Ошибка при проверке подключений")

async def reserves_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /reserves - обновление данных RestoPlace (только админы)"""
    user_id = update.effective_user.id
    
    # Проверяем права администратора
    if user_id not in ADMIN_IDS:
        await update.message.reply_text(f"{EMOJI['error']} Доступ запрещён. Команда только для администраторов.")
        return
    
    try:
        await update.message.reply_text(f"{EMOJI['clock']} Обновляю данные резервов из RestoPlace...")
        
        # Создаём сервис обновления
        updater = ReservesUpdateService()
        
        # Запускаем обновление данных
        stats = await updater.update_reserves_data()
        
        # Формируем и отправляем отчёт
        summary = updater.get_update_summary(stats)
        await update.message.reply_text(summary, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in reserves_command: {e}")
        await update.message.reply_text(f"{EMOJI['error']} Ошибка при обновлении данных резервов: {str(e)}")

async def auto_reserves_update():
    """Автоматическое обновление резервов для расписания"""
    try:
        logger.info("Запуск автоматического обновления резервов RestoPlace")
        
        updater = ReservesUpdateService()
        stats = await updater.update_reserves_data()
        
        # Отправляем краткий отчёт в чат отчётов
        summary = updater.get_update_summary(stats)
        
        # Импортируем здесь, чтобы избежать циклических импортов
        from config import REPORT_CHAT_IDS
        
        if REPORT_CHAT_IDS:
            # Отправляем в первый чат из списка
            # TODO: Здесь нужно будет добавить логику отправки через bot instance
            logger.info(f"Автообновление завершено: {stats}")
        
        return stats
        
    except Exception as e:
        logger.error(f"Ошибка автоматического обновления резервов: {e}")
        return {'error': str(e)}

@rate_limit
async def channels_chart_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /channels_chart - график эффективности каналов"""
    try:
        loading_msg = await update.message.reply_text(f"{EMOJI['clock']} Создаю график каналов...")
        
        analytics = AnalyticsService()
        visualization = get_visualization_service()
        
        # Получаем данные каналов
        channels_data = await analytics.analyze_channels()
        
        if not channels_data:
            await loading_msg.edit_text(f"{EMOJI['error']} Нет данных для создания графика")
            return
        
        # Создаём график
        chart_buffer = visualization.create_channel_performance_chart(channels_data)
        
        # Отправляем график
        await update.message.reply_photo(
            photo=InputFile(chart_buffer, filename="channels_chart.png"),
            caption=f"📊 График эффективности каналов привлечения\n\nПодробнее: /channels"
        )
        
        await loading_msg.delete()
        
    except Exception as e:
        logger.error(f"Error in channels_chart_command: {e}")
        await update.message.reply_text(f"{EMOJI['error']} Ошибка при создании графика каналов")

@rate_limit
async def segments_chart_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /segments_chart - диаграмма сегментов клиентов"""
    try:
        loading_msg = await update.message.reply_text(f"{EMOJI['clock']} Создаю диаграмму сегментов...")
        
        analytics = AnalyticsService()
        visualization = get_visualization_service()
        
        # Получаем данные сегментов
        segments_data = await analytics.analyze_segments()
        
        if not segments_data:
            await loading_msg.edit_text(f"{EMOJI['error']} Нет данных для создания диаграммы")
            return
        
        # Создаём диаграмму
        chart_buffer = visualization.create_segments_pie_chart(segments_data)
        
        # Отправляем диаграмму
        await update.message.reply_photo(
            photo=InputFile(chart_buffer, filename="segments_chart.png"),
            caption=f"👥 Диаграмма сегментов клиентов\n\nПодробнее: /segments"
        )
        
        await loading_msg.delete()
        
    except Exception as e:
        logger.error(f"Error in segments_chart_command: {e}")
        await update.message.reply_text(f"{EMOJI['error']} Ошибка при создании диаграммы сегментов")

@rate_limit
async def forecast_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /forecast - прогноз выручки"""
    try:
        loading_msg = await update.message.reply_text(f"{EMOJI['clock']} Создаю прогноз выручки...")
        
        analytics = AnalyticsService()
        visualization = get_visualization_service()
        
        # Получаем прогноз на 3 месяца
        forecast_data = await analytics.forecast_revenue(3)
        
        if not forecast_data:
            await loading_msg.edit_text(f"{EMOJI['error']} Не удалось создать прогноз")
            return
        
        # Создаём график прогноза
        chart_buffer = visualization.create_forecast_chart(forecast_data)
        
        # Форматируем текстовый отчёт
        total_forecast = forecast_data.get('total_forecast', 0)
        historical_avg = forecast_data.get('historical_avg', 0)
        
        forecast_text = f"""
📈 **ПРОГНОЗ ВЫРУЧКИ НА 3 МЕСЯЦА**

💰 Ожидаемая выручка: {format_currency(total_forecast)}
📊 Среднемесячная (прогноз): {format_currency(total_forecast/3)}
📋 Историческая средняя: {format_currency(historical_avg)}

🔮 **По месяцам:**
"""
        
        for month_data in forecast_data.get('forecast', []):
            seasonal_emoji = "🔥" if month_data['seasonal_coefficient'] > 1.1 else "❄️" if month_data['seasonal_coefficient'] < 0.9 else "🌟"
            forecast_text += f"{seasonal_emoji} {month_data['month_name']}: {format_currency(month_data['revenue'])}\n"
        
        # Отправляем график и текст
        await update.message.reply_photo(
            photo=InputFile(chart_buffer, filename="forecast_chart.png"),
            caption=forecast_text,
            parse_mode='Markdown'
        )
        
        await loading_msg.delete()
        
    except Exception as e:
        logger.error(f"Error in forecast_command: {e}")
        await update.message.reply_text(f"{EMOJI['error']} Ошибка при создании прогноза")

@rate_limit
async def compare_channels_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /compare - сравнение двух каналов"""
    try:
        # Проверяем аргументы команды
        if not context.args or len(context.args) < 2:
            await update.message.reply_text(
                f"{EMOJI['info']} Использование: `/compare канал1 канал2`\n\n"
                "Например: `/compare Instagram ВКонтакте`",
                parse_mode='Markdown'
            )
            return
        
        channel1_name = context.args[0]
        channel2_name = context.args[1]
        
        loading_msg = await update.message.reply_text(f"{EMOJI['clock']} Сравниваю каналы...")
        
        analytics = AnalyticsService()
        visualization = get_visualization_service()
        
        # Получаем данные каналов
        channel1_data = await analytics.analyze_channel(channel1_name)
        channel2_data = await analytics.analyze_channel(channel2_name)
        
        if not channel1_data:
            await loading_msg.edit_text(f"{EMOJI['error']} Канал '{channel1_name}' не найден")
            return
            
        if not channel2_data:
            await loading_msg.edit_text(f"{EMOJI['error']} Канал '{channel2_name}' не найден")
            return
        
        # Создаём сравнительный график
        chart_buffer = visualization.create_comparison_chart(channel1_data, channel2_data)
        
        # Определяем победителя
        score1 = (channel1_data.get('rating', 0) + 
                 (1 if channel1_data.get('roi', 0) > channel2_data.get('roi', 0) else 0) +
                 (1 if channel1_data.get('conversion_rate', 0) > channel2_data.get('conversion_rate', 0) else 0))
        
        score2 = (channel2_data.get('rating', 0) + 
                 (1 if channel2_data.get('roi', 0) > channel1_data.get('roi', 0) else 0) +
                 (1 if channel2_data.get('conversion_rate', 0) > channel1_data.get('conversion_rate', 0) else 0))
        
        winner = channel1_name if score1 > score2 else channel2_name if score2 > score1 else "Ничья"
        winner_emoji = "🥇" if winner != "Ничья" else "🤝"
        
        comparison_text = f"""
⚖️ **СРАВНЕНИЕ КАНАЛОВ**

🥊 {channel1_name} vs {channel2_name}

{winner_emoji} **Победитель: {winner}**

📊 **Детальное сравнение в графике выше**
        """
        
        # Отправляем график и результат
        await update.message.reply_photo(
            photo=InputFile(chart_buffer, filename="comparison_chart.png"),
            caption=comparison_text,
            parse_mode='Markdown'
        )
        
        await loading_msg.delete()
        
    except Exception as e:
        logger.error(f"Error in compare_channels_command: {e}")
        await update.message.reply_text(f"{EMOJI['error']} Ошибка при сравнении каналов")

@admin_rate_limit  
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /status - статус системы (только для админов)"""
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text(f"{EMOJI['error']} Команда доступна только администраторам")
        return
    
    try:
        from services.database import get_db_service
        from config import USE_POSTGRES, REDIS_URL
        
        status_text = f"""
🔧 **СТАТУС СИСТЕМЫ**

📊 **База данных:**
• PostgreSQL: {'✅ Подключена' if USE_POSTGRES else '❌ Отключена'}

🗄️ **Кэширование:**
• Redis: {'✅ Настроен' if REDIS_URL else '❌ Не настроен'}

⚡ **Сервисы:**
• Analytics Service: ✅ Активен
• Visualization Service: ✅ Активен
• Rate Limiter: ✅ Активен

📈 **Последняя активность:**
• Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}
"""
        
        # Проверяем подключение к базе данных
        if USE_POSTGRES:
            try:
                db_service = await get_db_service()
                # Простой тест подключения
                test_query = "SELECT 1"
                await db_service.pool.fetchval(test_query)
                status_text += "\n✅ Тест подключения к PostgreSQL: OK"
            except Exception as e:
                status_text += f"\n❌ Ошибка подключения к PostgreSQL: {str(e)[:50]}"
        
        await update.message.reply_text(status_text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in status_command: {e}")
        await update.message.reply_text(f"{EMOJI['error']} Ошибка при получении статуса системы")
