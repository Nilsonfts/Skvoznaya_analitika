"""
Клавиатуры и кнопки для Telegram-бота
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

# Основное меню с кнопками
def get_main_menu():
    """Основное меню с кнопками"""
    keyboard = [
        [
            KeyboardButton("📊 Отчёты"),
            KeyboardButton("📈 Аналитика")
        ],
        [
            KeyboardButton("🎯 Каналы"),
            KeyboardButton("👥 Сегменты")
        ],
        [
            KeyboardButton("⚙️ Управление"),
            KeyboardButton("📱 Помощь")
        ]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

# Меню отчётов
def get_reports_menu():
    """Меню отчётов"""
    keyboard = [
        [
            InlineKeyboardButton("📋 Ежедневный отчёт", callback_data="report_daily"),
            InlineKeyboardButton("📊 Прогноз выручки", callback_data="report_forecast")
        ],
        [
            InlineKeyboardButton("📈 Сравнение каналов", callback_data="report_compare"),
            InlineKeyboardButton("📉 Статус системы", callback_data="report_status")
        ],
        [
            InlineKeyboardButton("🔙 Назад", callback_data="main_menu")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# Меню аналитики
def get_analytics_menu():
    """Меню аналитики"""
    keyboard = [
        [
            InlineKeyboardButton("📊 График каналов", callback_data="analytics_channels_chart"),
            InlineKeyboardButton("🥧 Диаграмма сегментов", callback_data="analytics_segments_chart")
        ],
        [
            InlineKeyboardButton("📈 Визуализация прогноза", callback_data="analytics_forecast_chart"),
            InlineKeyboardButton("🔍 Тест Метрики", callback_data="analytics_test_metrika")
        ],
        [
            InlineKeyboardButton("🔙 Назад", callback_data="main_menu")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# Меню каналов
def get_channels_menu():
    """Меню каналов привлечения"""
    keyboard = [
        [
            InlineKeyboardButton("📊 Анализ всех каналов", callback_data="channels_all"),
            InlineKeyboardButton("📈 График эффективности", callback_data="channels_chart")
        ],
        [
            InlineKeyboardButton("🔍 Детальный анализ канала", callback_data="channels_detail"),
            InlineKeyboardButton("⚖️ Сравнение каналов", callback_data="channels_compare")
        ],
        [
            InlineKeyboardButton("🔙 Назад", callback_data="main_menu")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# Меню сегментов
def get_segments_menu():
    """Меню сегментации клиентов"""
    keyboard = [
        [
            InlineKeyboardButton("👥 Анализ сегментов", callback_data="segments_analysis"),
            InlineKeyboardButton("🥧 Диаграмма сегментов", callback_data="segments_chart")
        ],
        [
            InlineKeyboardButton("👨‍💼 Эффективность менеджеров", callback_data="segments_managers"),
            InlineKeyboardButton("🎯 VIP-клиенты", callback_data="segments_vip")
        ],
        [
            InlineKeyboardButton("🔙 Назад", callback_data="main_menu")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# Меню управления (только для админов)
def get_admin_menu():
    """Меню управления для администраторов"""
    keyboard = [
        [
            InlineKeyboardButton("🔄 Обновить данные", callback_data="admin_update"),
            InlineKeyboardButton("🏨 Резервы RestoPlace", callback_data="admin_reserves")
        ],
        [
            InlineKeyboardButton("🔔 Уведомления ON/OFF", callback_data="admin_alerts"),
            InlineKeyboardButton("📊 Статус системы", callback_data="admin_status")
        ],
        [
            InlineKeyboardButton("🧪 Тест Google Sheets", callback_data="admin_test_sheets"),
            InlineKeyboardButton("🔍 Тест Яндекс.Метрики", callback_data="admin_test_metrika")
        ],
        [
            InlineKeyboardButton("🔧 Тест всех подключений", callback_data="admin_test_all")
        ],
        [
            InlineKeyboardButton("🔙 Назад", callback_data="main_menu")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# Меню помощи
def get_help_menu():
    """Меню помощи"""
    keyboard = [
        [
            InlineKeyboardButton("📖 Справка по командам", callback_data="help_commands"),
            InlineKeyboardButton("🎯 Что такое CAC/LTV", callback_data="help_metrics")
        ],
        [
            InlineKeyboardButton("📊 Как читать отчёты", callback_data="help_reports"),
            InlineKeyboardButton("🎤 О караоке-рюмочной", callback_data="help_about")
        ],
        [
            InlineKeyboardButton("🔙 Назад", callback_data="main_menu")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# Быстрые действия
def get_quick_actions():
    """Быстрые действия"""
    keyboard = [
        [
            InlineKeyboardButton("⚡ Быстрый отчёт", callback_data="quick_report"),
            InlineKeyboardButton("📈 Топ-каналы", callback_data="quick_channels")
        ],
        [
            InlineKeyboardButton("🎯 Сегодняшние лиды", callback_data="quick_today"),
            InlineKeyboardButton("💰 Прогноз месяца", callback_data="quick_forecast")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# Подтверждение действий
def get_confirmation_menu(action):
    """Меню подтверждения действия"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Да, выполнить", callback_data=f"confirm_{action}"),
            InlineKeyboardButton("❌ Отмена", callback_data="main_menu")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# Навигация по периодам
def get_period_menu():
    """Меню выбора периода"""
    keyboard = [
        [
            InlineKeyboardButton("📅 Сегодня", callback_data="period_today"),
            InlineKeyboardButton("📅 Вчера", callback_data="period_yesterday")
        ],
        [
            InlineKeyboardButton("📅 Неделя", callback_data="period_week"),
            InlineKeyboardButton("📅 Месяц", callback_data="period_month")
        ],
        [
            InlineKeyboardButton("📅 Произвольный", callback_data="period_custom"),
            InlineKeyboardButton("🔙 Назад", callback_data="main_menu")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
