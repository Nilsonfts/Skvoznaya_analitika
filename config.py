"""
Конфигурация Telegram-бота для маркетинговой аналитики "Евгенич СПБ"
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Telegram Bot Token
BOT_TOKEN = os.getenv('BOT_TOKEN', os.getenv('TELEGRAM_TOKEN', ''))

# Google Sheets конфигурация
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID', "1QL1CRY3M9Av-WlDS5gswA2Lq14OPdt0TME_dpwPIuC4")
GOOGLE_CREDENTIALS_FILE = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
GOOGLE_CREDENTIALS_JSON = os.getenv('GOOGLE_CREDENTIALS_JSON', '')  # Для прямой передачи JSON

# AmoCRM интеграция (опционально)
AMOCRM_SHEET_ID = os.getenv('AMOCRM_SHEET_ID', '')

# Яндекс.Метрика конфигурация
METRIKA_COUNTER_ID = os.getenv('METRIKA_COUNTER_ID', "101368505")
METRIKA_OAUTH_TOKEN = os.getenv('METRIKA_OAUTH_TOKEN', os.getenv('METRIKA_ACCESS_TOKEN', ''))

# Google Analytics конфигурация (опционально)
GA_PROPERTY_ID = os.getenv('GA_PROPERTY_ID', '')
GA_CREDENTIALS_JSON = os.getenv('GA_CREDENTIALS_JSON', '')
GA_MEASUREMENT_ID = os.getenv('GA_MEASUREMENT_ID', '')
GA_API_SECRET = os.getenv('GA_API_SECRET', '')

# RestoPlace интеграция
RESTOPLACE_API_KEY = os.getenv('RESTOPLACE_API_KEY', '')

# Telegram ID администраторов и чатов для отчетов
ADMIN_IDS = [int(x.strip()) for x in os.getenv('ADMIN_IDS', '').split(',') if x.strip()]
REPORT_CHAT_IDS = [x.strip() for x in os.getenv('REPORT_CHAT_ID', '').split(',') if x.strip()]
SMM_IDS = [int(x.strip()) for x in os.getenv('SMM_IDS', '').split(',') if x.strip()]

# База данных PostgreSQL (опционально)
USE_POSTGRES = os.getenv('USE_POSTGRES', 'false').lower() == 'true'
DATABASE_URL = os.getenv('DATABASE_URL', '')

# Настройки Redis и кэширования
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
REDIS_DB = int(os.getenv('REDIS_DB', '0'))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')
REDIS_URL = os.getenv('REDIS_URL', f'redis://{":" + REDIS_PASSWORD + "@" if REDIS_PASSWORD else ""}{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}')

# Обработка Railway Redis URL
if 'REDIS_URL' in os.environ and not REDIS_URL.startswith('redis://'):
    # Railway может предоставить URL в другом формате
    REDIS_URL = os.environ['REDIS_URL']

# Rate Limiting
RATE_LIMIT_PER_MINUTE = int(os.getenv('RATE_LIMIT_PER_MINUTE', '10'))

# Настройки расписания и уведомлений
DAILY_REPORT_TIME = os.getenv('DAILY_REPORT_TIME', '09:00')
WEEKLY_REPORT_DAY = os.getenv('WEEKLY_REPORT_DAY', 'monday')
MONTHLY_REPORT_DAY = int(os.getenv('MONTHLY_REPORT_DAY', '1'))
TIMEZONE = os.getenv('TIMEZONE', 'Europe/Moscow')

# Дополнительные настройки
DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
MAX_CONCURRENT_REQUESTS = int(os.getenv('MAX_CONCURRENT_REQUESTS', '10'))
REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '30'))

# Конфигурация листов Google Sheets
SHEETS_CONFIG = {
    'leads_site': 'Заявки Сайт',
    'leads_social': 'Заявки Соц сети',
    'guests': 'Guests RP',
    'analytics': 'Маркетинг Аналитика',
    'dashboard': '🎯 Главный дашборд',
    'channels_analysis': '📊 Анализ каналов',
    'segments_analysis': '👥 Сегменты клиентов',
    'metrika_analysis': '📊 Анализ Метрики',
    'managers_analysis': '👤 Менеджеры',
    'conversion_funnel': 'Воронка Конверсии'
}

# Настройки расходов по каналам (в месяц, в рублях)
CHANNEL_COSTS = {
    'Yandex': 50000,
    'Google': 40000,
    'VKontakte': 20000,
    'Instagram': 15000,
    'Facebook': 15000,
    'Telegram': 5000,
    '2GIS': 10000,
    'Yandex Maps': 5000,
    'Direct': 1000,
    'Other': 1000
}

# Настройки сегментации клиентов
SEGMENT_CONFIG = {
    'VIP': {
        'min_visits': 10,
        'min_revenue': 100000,
        'color': '#FFD700',
        'emoji': '👑'
    },
    'REGULAR': {
        'min_visits': 5,
        'min_revenue': 50000,
        'color': '#90EE90',
        'emoji': '⭐'
    },
    'RETURNING': {
        'min_visits': 2,
        'min_revenue': 0,
        'color': '#87CEEB',
        'emoji': '🔄'
    },
    'NEW': {
        'min_visits': 1,
        'min_revenue': 0,
        'color': '#FFE4B5',
        'emoji': '🆕'
    }
}

# Настройки LTV расчётов
LTV_CONFIG = {
    'max_visits_per_year': 6,
    'forecast_years': 2
}

# Настройки автоматических уведомлений
ALERTS_CONFIG = {
    'conversion_drop_threshold': 0.25,  # 25% снижение конверсии
    'roi_threshold': -50,  # ROI ниже -50%
    'new_vip_notify': True,
    'daily_report_time': '09:00'
}

# Настройки Redis (если используется)
REDIS_CONFIG = {
    'host': os.getenv('REDIS_HOST', 'localhost'),
    'port': int(os.getenv('REDIS_PORT', '6379')),
    'db': int(os.getenv('REDIS_DB', '0')),
    'password': os.getenv('REDIS_PASSWORD', None)
}

# Маппинг каналов на основе UTM меток
CHANNEL_MAPPING = {
    'yandex': 'Yandex',
    'google': 'Google',
    'instagram': 'Instagram',
    'facebook': 'Facebook',
    'vk': 'VKontakte',
    'vkontakte': 'VKontakte',
    'telegram': 'Telegram',
    '2gis': '2GIS',
    'yandex.maps': 'Yandex Maps',
    'maps': 'Yandex Maps',
    'direct': 'Direct',
    'organic': 'Direct'
}

# Конфигурация столбцов для источников данных
LEAD_SOURCES = {
    'site': {
        'sheet_name': 'Заявки Сайт',
        'columns': {
            'date': 'Date',
            'name': 'Name',
            'phone': 'Очищенный телефон',  # Точное название без переноса строки
            'email': 'Email',
            'utm_source': 'utm_source',
            'utm_medium': 'utm_medium',
            'utm_campaign': 'utm_campaign',
            'utm_content': 'utm_content',
            'utm_term': 'utm_term',
            'ga_client_id': 'ga_client_id',
            'ym_client_id': 'ym_client_id',
            'form_name': 'Form name',
            'button_text': 'button_text'
        }
    },
    'social': {
        'sheet_name': 'Заявки Соц сети',
        'columns': {
            'date': 'Дата Заявки',
            'name': 'Имя Гостя',
            'phone': 'Телефон',
            'email': 'Email',  # Может быть пустым
            'utm_source': 'UTM Source (Источник)',
            'utm_medium': 'UTM Medium (Канал)',
            'utm_campaign': 'UTM Campaign (Кампания)',
            'utm_content': 'UTM Content (Содержание)',
            'utm_term': 'UTM Term (Ключ/Дата)',
            'ga_client_id': 'ga_id',  # Может быть пустым
            'ym_client_id': 'ym_id'   # Может быть пустым
        }
    },
    'guests': {
        'sheet_name': 'Guests RP',
        'columns': {
            'name': 'Имя',
            'phone': 'Телефон',
            'email': 'Email',
            'visits_count': 'Кол-во визитов',
            'total_revenue': 'Общая сумма',
            'first_visit': 'Первый визит',
            'last_visit': 'Последний визит',
            'visit_1': 'Счёт 1-го визита',
            'visit_2': 'Счёт 2-го визита',
            'visit_3': 'Счёт 3-го визита',
            'visit_4': 'Счёт 4-го визита',
            'visit_5': 'Счёт 5-го визита',
            'visit_6': 'Счёт 6-го визита',
            'visit_7': 'Счёт 7-го визита',
            'visit_8': 'Счёт 8-го визита',
            'visit_9': 'Счёт 9-го визита',
            'visit_10': 'Счёт 10-го визита'
        }
    }
}

# Структура итоговой таблицы "Маркетинг Аналитика"
ANALYTICS_TABLE_STRUCTURE = [
    'ID',                # ID лида (LEAD_xxx)
    'Дата заявки',       # Дата заявки
    'Имя',               # Имя клиента
    'Телефон',           # Очищенный номер телефона
    'Email',             # Email адрес
    'Исходный лист',     # Заявки Сайт или Заявки Соц сети
    'utm_source',        # UTM метки
    'utm_medium',
    'utm_campaign',
    'utm_content',
    'utm_term',
    'GA Client ID',      # Google Analytics Client ID
    'YM Client ID',      # Яндекс.Метрика Client ID
    'Форма',             # Название формы
    'Кнопка',            # Текст кнопки
    'Канал',             # Определенный канал привлечения
    'Статус',            # Статус клиента
    'Сегмент',           # Сегмент клиента
    'Визитов',           # Количество визитов
    'Выручка ₽',         # Общая выручка от клиента
    'Средний чек ₽',     # Средний чек клиента
    'Первый визит',      # Дата первого визита
    'Последний визит',   # Дата последнего визита
    'LTV ₽',             # Lifetime Value
    'Дней с первого визита',  # Количество дней с первого визита
    # Метрики Яндекс.Метрики
    'YM Визиты',         # Количество визитов в Метрике
    'YM Просмотры',      # Количество просмотров страниц
    'YM Отказы %',       # Процент отказов
    'YM Время (сек)'     # Время на сайте в секундах
]

# Настройки API Яндекс.Метрики
METRIKA_API_CONFIG = {
    'base_url': 'https://api-metrika.yandex.net',
    'batch_size': 10,  # Количество лидов в одном запросе
    'request_delay': 1,  # Задержка между запросами в секундах
    'metrics': [
        'ym:s:visits',
        'ym:s:pageviews', 
        'ym:s:bounceRate',
        'ym:s:avgVisitDuration'
    ]
}

# Цветовая схема для дашбордов
COLORS = {
    'primary': '#4A90E2',
    'success': '#7ED321',
    'warning': '#F5A623',
    'danger': '#D0021B',
    'info': '#50E3C2',
    'light': '#F8F9FA',
    'dark': '#343A40'
}

# Emoji для использования в сообщениях
EMOJI = {
    'report': '📊',
    'money': '💰',
    'chart_up': '📈',
    'chart_down': '📉',
    'warning': '⚠️',
    'success': '✅',
    'error': '❌',
    'info': 'ℹ️',
    'crown': '👑',
    'star': '⭐',
    'fire': '🔥',
    'rocket': '🚀',
    'calendar': '📅',
    'clock': '🕐',
    'users': '👥',
    'new': '🆕',
    'top': '🏆'
}
