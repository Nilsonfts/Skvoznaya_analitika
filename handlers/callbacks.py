"""
Обработчики callback'ов для кнопок
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from config import EMOJI, ADMIN_IDS
from handlers.keyboards import (
    get_main_menu, get_reports_menu, get_analytics_menu, 
    get_channels_menu, get_segments_menu, get_admin_menu, 
    get_help_menu, get_quick_actions, get_period_menu
)
from handlers.commands import (
    report_command, channels_command, segments_command, 
    managers_command, update_command, forecast_command,
    alerts_command, reserves_command, channels_chart_command,
    segments_chart_command, compare_channels_command,
    status_command, test_metrika_command, test_google_sheets_command,
    test_all_connections_command
)

logger = logging.getLogger(__name__)

async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик нажатий на кнопки"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    data = query.data
    
    try:
        # Главное меню
        if data == "main_menu":
            await query.edit_message_text(
                text="🎤 **Караоке-рюмочная 'Евгенич СПБ'**\n\nВыберите раздел:",
                parse_mode='Markdown',
                reply_markup=get_main_menu()
            )
            
        # === ОТЧЁТЫ ===
        elif data == "reports_menu":
            await query.edit_message_text(
                text="📊 **ОТЧЁТЫ**\n\nВыберите тип отчёта:",
                parse_mode='Markdown',
                reply_markup=get_reports_menu()
            )
            
        elif data == "report_daily":
            await query.edit_message_text("📋 Генерирую ежедневный отчёт...")
            # Создаём фейковый Update для команды
            fake_update = type('FakeUpdate', (), {
                'message': type('FakeMessage', (), {
                    'reply_text': lambda self, text, **kwargs: query.edit_message_text(text, **kwargs)
                })(),
                'effective_user': update.effective_user
            })()
            await report_command(fake_update, context)
            
        elif data == "report_forecast":
            await query.edit_message_text("📈 Генерирую прогноз выручки...")
            fake_update = type('FakeUpdate', (), {
                'message': type('FakeMessage', (), {
                    'reply_text': lambda self, text, **kwargs: query.edit_message_text(text, **kwargs)
                })(),
                'effective_user': update.effective_user
            })()
            await forecast_command(fake_update, context)
            
        elif data == "report_compare":
            await query.edit_message_text("⚖️ Сравниваю каналы...")
            fake_update = type('FakeUpdate', (), {
                'message': type('FakeMessage', (), {
                    'reply_text': lambda self, text, **kwargs: query.edit_message_text(text, **kwargs)
                })(),
                'effective_user': update.effective_user
            })()
            await compare_channels_command(fake_update, context)
            
        elif data == "report_status":
            await query.edit_message_text("📊 Проверяю статус системы...")
            fake_update = type('FakeUpdate', (), {
                'message': type('FakeMessage', (), {
                    'reply_text': lambda self, text, **kwargs: query.edit_message_text(text, **kwargs)
                })(),
                'effective_user': update.effective_user
            })()
            await status_command(fake_update, context)
            
        # === АНАЛИТИКА ===
        elif data == "analytics_menu":
            await query.edit_message_text(
                text="📈 **АНАЛИТИКА И ВИЗУАЛИЗАЦИЯ**\n\nВыберите тип анализа:",
                parse_mode='Markdown',
                reply_markup=get_analytics_menu()
            )
            
        elif data == "analytics_channels_chart":
            await query.edit_message_text("📊 Создаю график каналов...")
            fake_update = type('FakeUpdate', (), {
                'message': type('FakeMessage', (), {
                    'reply_text': lambda self, text, **kwargs: query.edit_message_text(text, **kwargs),
                    'reply_photo': lambda self, photo, **kwargs: query.message.reply_photo(photo, **kwargs)
                })(),
                'effective_user': update.effective_user
            })()
            await channels_chart_command(fake_update, context)
            
        elif data == "analytics_segments_chart":
            await query.edit_message_text("🥧 Создаю диаграмму сегментов...")
            fake_update = type('FakeUpdate', (), {
                'message': type('FakeMessage', (), {
                    'reply_text': lambda text, **kwargs: query.edit_message_text(text, **kwargs),
                    'reply_photo': lambda photo, **kwargs: query.message.reply_photo(photo, **kwargs)
                })(),
                'effective_user': update.effective_user
            })()
            await segments_chart_command(fake_update, context)
            
        elif data == "analytics_test_metrika":
            await query.edit_message_text("🔍 Тестирую подключение к Яндекс.Метрике...")
            fake_update = type('FakeUpdate', (), {
                'message': type('FakeMessage', (), {
                    'reply_text': lambda text, **kwargs: query.edit_message_text(text, **kwargs)
                })(),
                'effective_user': update.effective_user
            })()
            await test_metrika_command(fake_update, context)
            
        # === КАНАЛЫ ===
        elif data == "channels_menu":
            await query.edit_message_text(
                text="🎯 **КАНАЛЫ ПРИВЛЕЧЕНИЯ**\n\nВыберите действие:",
                parse_mode='Markdown',
                reply_markup=get_channels_menu()
            )
            
        elif data == "channels_all":
            await query.edit_message_text("📊 Анализирую все каналы привлечения...")
            fake_update = type('FakeUpdate', (), {
                'message': type('FakeMessage', (), {
                    'reply_text': lambda text, **kwargs: query.edit_message_text(text, **kwargs)
                })(),
                'effective_user': update.effective_user
            })()
            await channels_command(fake_update, context)
            
        elif data == "channels_chart":
            await query.edit_message_text("📈 Создаю график эффективности каналов...")
            fake_update = type('FakeUpdate', (), {
                'message': type('FakeMessage', (), {
                    'reply_text': lambda text, **kwargs: query.edit_message_text(text, **kwargs),
                    'reply_photo': lambda photo, **kwargs: query.message.reply_photo(photo, **kwargs)
                })(),
                'effective_user': update.effective_user
            })()
            await channels_chart_command(fake_update, context)
            
        elif data == "channels_compare":
            await query.edit_message_text("⚖️ Сравниваю эффективность каналов...")
            fake_update = type('FakeUpdate', (), {
                'message': type('FakeMessage', (), {
                    'reply_text': lambda text, **kwargs: query.edit_message_text(text, **kwargs)
                })(),
                'effective_user': update.effective_user
            })()
            await compare_channels_command(fake_update, context)
            
        # === СЕГМЕНТЫ ===
        elif data == "segments_menu":
            await query.edit_message_text(
                text="👥 **СЕГМЕНТАЦИЯ КЛИЕНТОВ**\n\nВыберите анализ:",
                parse_mode='Markdown',
                reply_markup=get_segments_menu()
            )
            
        elif data == "segments_analysis":
            await query.edit_message_text("👥 Анализирую сегменты клиентов...")
            fake_update = type('FakeUpdate', (), {
                'message': type('FakeMessage', (), {
                    'reply_text': lambda text, **kwargs: query.edit_message_text(text, **kwargs)
                })(),
                'effective_user': update.effective_user
            })()
            await segments_command(fake_update, context)
            
        elif data == "segments_chart":
            await query.edit_message_text("🥧 Создаю диаграмму сегментов...")
            fake_update = type('FakeUpdate', (), {
                'message': type('FakeMessage', (), {
                    'reply_text': lambda text, **kwargs: query.edit_message_text(text, **kwargs),
                    'reply_photo': lambda photo, **kwargs: query.message.reply_photo(photo, **kwargs)
                })(),
                'effective_user': update.effective_user
            })()
            await segments_chart_command(fake_update, context)
            
        elif data == "segments_managers":
            await query.edit_message_text("👨‍💼 Анализирую эффективность менеджеров...")
            fake_update = type('FakeUpdate', (), {
                'message': type('FakeMessage', (), {
                    'reply_text': lambda text, **kwargs: query.edit_message_text(text, **kwargs)
                })(),
                'effective_user': update.effective_user
            })()
            await managers_command(fake_update, context)
            
        # === УПРАВЛЕНИЕ (АДМИНЫ) ===
        elif data == "admin_menu":
            if user_id not in ADMIN_IDS:
                await query.edit_message_text(
                    f"{EMOJI['error']} Доступ запрещён. Раздел только для администраторов."
                )
                return
                
            await query.edit_message_text(
                text="⚙️ **УПРАВЛЕНИЕ СИСТЕМОЙ**\n\nВыберите действие:",
                parse_mode='Markdown',
                reply_markup=get_admin_menu()
            )
            
        elif data == "admin_update":
            if user_id not in ADMIN_IDS:
                await query.edit_message_text(f"{EMOJI['error']} Доступ запрещён.")
                return
                
            await query.edit_message_text("🔄 Обновляю данные...")
            fake_update = type('FakeUpdate', (), {
                'message': type('FakeMessage', (), {
                    'reply_text': lambda text, **kwargs: query.edit_message_text(text, **kwargs)
                })(),
                'effective_user': update.effective_user
            })()
            await update_command(fake_update, context)
            
        elif data == "admin_reserves":
            if user_id not in ADMIN_IDS:
                await query.edit_message_text(f"{EMOJI['error']} Доступ запрещён.")
                return
                
            await query.edit_message_text("🏨 Обновляю данные RestoPlace...")
            fake_update = type('FakeUpdate', (), {
                'message': type('FakeMessage', (), {
                    'reply_text': lambda text, **kwargs: query.edit_message_text(text, **kwargs)
                })(),
                'effective_user': update.effective_user
            })()
            await reserves_command(fake_update, context)
            
        elif data == "admin_alerts":
            if user_id not in ADMIN_IDS:
                await query.edit_message_text(f"{EMOJI['error']} Доступ запрещён.")
                return
                
            await query.edit_message_text("🔔 Управляю уведомлениями...")
            fake_update = type('FakeUpdate', (), {
                'message': type('FakeMessage', (), {
                    'reply_text': lambda text, **kwargs: query.edit_message_text(text, **kwargs)
                })(),
                'effective_user': update.effective_user
            })()
            await alerts_command(fake_update, context)
            
        elif data == "admin_test_sheets":
            if user_id not in ADMIN_IDS:
                await query.edit_message_text(f"{EMOJI['error']} Доступ запрещён.")
                return
                
            await query.edit_message_text("🧪 Тестирую подключение к Google Sheets...")
            fake_update = type('FakeUpdate', (), {
                'message': type('FakeMessage', (), {
                    'reply_text': lambda text, **kwargs: query.edit_message_text(text, **kwargs)
                })(),
                'effective_user': update.effective_user
            })()
            await test_google_sheets_command(fake_update, context)
            
        elif data == "admin_test_metrika":
            if user_id not in ADMIN_IDS:
                await query.edit_message_text(f"{EMOJI['error']} Доступ запрещён.")
                return
                
            await query.edit_message_text("🔍 Тестирую подключение к Яндекс.Метрике...")
            fake_update = type('FakeUpdate', (), {
                'message': type('FakeMessage', (), {
                    'reply_text': lambda text, **kwargs: query.edit_message_text(text, **kwargs)
                })(),
                'effective_user': update.effective_user
            })()
            await test_metrika_command(fake_update, context)
            
        elif data == "admin_test_all":
            if user_id not in ADMIN_IDS:
                await query.edit_message_text(f"{EMOJI['error']} Доступ запрещён.")
                return
                
            await query.edit_message_text("🔧 Тестирую все подключения...")
            fake_update = type('FakeUpdate', (), {
                'message': type('FakeMessage', (), {
                    'reply_text': lambda text, **kwargs: query.edit_message_text(text, **kwargs)
                })(),
                'effective_user': update.effective_user
            })()
            await test_all_connections_command(fake_update, context)
            
        # === ПОМОЩЬ ===
        elif data == "help_menu":
            await query.edit_message_text(
                text="📱 **СПРАВОЧНАЯ ИНФОРМАЦИЯ**\n\nВыберите раздел:",
                parse_mode='Markdown',
                reply_markup=get_help_menu()
            )
            
        elif data == "help_commands":
            help_text = f"""
📖 **СПРАВКА ПО КОМАНДАМ**

{EMOJI['chart_up']} **Отчёты:**
• Ежедневный отчёт - основные показатели за день
• Прогноз выручки - предсказание доходов с учётом сезонности
• Сравнение каналов - эффективность привлечения

{EMOJI['target']} **Аналитика:**
• График каналов - визуализация эффективности
• Диаграмма сегментов - распределение клиентов
• Тест Метрики - проверка подключения

{EMOJI['people']} **Клиенты:**
• Сегментация - анализ групп клиентов
• Менеджеры - эффективность работы
• VIP-клиенты - ценные клиенты

{EMOJI['gear']} **Управление (админы):**
• Обновление данных - синхронизация
• RestoPlace - интеграция бронирований
• Уведомления - настройка алертов
"""
            await query.edit_message_text(help_text, parse_mode='Markdown', reply_markup=get_help_menu())
            
        elif data == "help_metrics":
            metrics_text = f"""
🎯 **МЕТРИКИ КАРАОКЕ-РЮМОЧНОЙ**

💰 **CAC (Customer Acquisition Cost):**
Стоимость привлечения одного клиента
= Расходы на рекламу / Количество новых клиентов

💎 **LTV (Lifetime Value):**
Жизненная ценность клиента
= Средний чек × Частота визитов × Период жизни

📊 **ROI (Return on Investment):**
Возврат инвестиций
= (Доход - Расходы) / Расходы × 100%

🎤 **Сезонность караоке:**
• Декабрь: +50% (корпоративы)
• Лето: -10% (отпуска)  
• Пятница-суббота: пик активности
• Понедельник-вторник: минимум

📈 **Конверсия:**
Процент посетителей, ставших клиентами
"""
            await query.edit_message_text(metrics_text, parse_mode='Markdown', reply_markup=get_help_menu())
            
        elif data == "help_about":
            about_text = f"""
🎤 **О КАРАОКЕ-РЮМОЧНОЙ "ЕВГЕНИЧ СПБ"**

Современное заведение развлекательного формата в Санкт-Петербурге, сочетающее:

🍻 **Атмосфера:**
• Уютная рюмочная с домашней атмосферой
• Профессиональное караоке-оборудование
• Комфортные залы для компаний

🎯 **Особенности бизнеса:**
• Сезонные колебания спроса
• Зависимость от дней недели
• Корпоративные мероприятия
• Приватные вечеринки

📊 **Аналитика помогает:**
• Планировать загрузку залов
• Оптимизировать рекламный бюджет
• Прогнозировать выручку
• Улучшать сервис
"""
            await query.edit_message_text(about_text, parse_mode='Markdown', reply_markup=get_help_menu())
            
        # Обработка неизвестных callback'ов
        else:
            await query.edit_message_text(
                f"{EMOJI['error']} Неизвестная команда. Возвращаюсь в главное меню.",
                reply_markup=get_main_menu()
            )
            
    except Exception as e:
        logger.error(f"Ошибка в callback handler: {e}")
        await query.edit_message_text(
            f"{EMOJI['error']} Произошла ошибка. Попробуйте ещё раз.",
            reply_markup=get_main_menu()
        )

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик текстовых сообщений с кнопок"""
    text = update.message.text
    user_id = update.effective_user.id
    
    try:
        if text == "📊 Отчёты":
            await update.message.reply_text(
                "📊 **ОТЧЁТЫ**\n\nВыберите тип отчёта:",
                parse_mode='Markdown',
                reply_markup=get_reports_menu()
            )
            
        elif text == "📈 Аналитика":
            await update.message.reply_text(
                "📈 **АНАЛИТИКА И ВИЗУАЛИЗАЦИЯ**\n\nВыберите тип анализа:",
                parse_mode='Markdown',
                reply_markup=get_analytics_menu()
            )
            
        elif text == "🎯 Каналы":
            await update.message.reply_text(
                "🎯 **КАНАЛЫ ПРИВЛЕЧЕНИЯ**\n\nВыберите действие:",
                parse_mode='Markdown',
                reply_markup=get_channels_menu()
            )
            
        elif text == "👥 Сегменты":
            await update.message.reply_text(
                "👥 **СЕГМЕНТАЦИЯ КЛИЕНТОВ**\n\nВыберите анализ:",
                parse_mode='Markdown',
                reply_markup=get_segments_menu()
            )
            
        elif text == "⚙️ Управление":
            if user_id not in ADMIN_IDS:
                await update.message.reply_text(
                    f"{EMOJI['error']} Доступ запрещён. Раздел только для администраторов."
                )
                return
                
            await update.message.reply_text(
                "⚙️ **УПРАВЛЕНИЕ СИСТЕМОЙ**\n\nВыберите действие:",
                parse_mode='Markdown',
                reply_markup=get_admin_menu()
            )
            
        elif text == "📱 Помощь":
            await update.message.reply_text(
                "📱 **СПРАВОЧНАЯ ИНФОРМАЦИЯ**\n\nВыберите раздел:",
                parse_mode='Markdown',
                reply_markup=get_help_menu()
            )
            
        else:
            # Быстрые команды
            quick_actions_text = f"""
⚡ **БЫСТРЫЕ ДЕЙСТВИЯ**

Используйте кнопки меню или быстрые действия:
"""
            await update.message.reply_text(
                quick_actions_text,
                parse_mode='Markdown',
                reply_markup=get_quick_actions()
            )
            
    except Exception as e:
        logger.error(f"Ошибка в message handler: {e}")
        await update.message.reply_text(
            f"{EMOJI['error']} Произошла ошибка. Попробуйте ещё раз."
        )
