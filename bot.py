#!/usr/bin/env python3
"""
Telegram-бот для маркетинговой аналитики "Евгенич СПБ"
Основной файл запуска бота
"""

import logging
import asyncio
import json
from datetime import datetime, time
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import (
    Application, 
    CommandHandler, 
    ContextTypes, 
    MessageHandler,
    filters
)

from config import BOT_TOKEN, ADMIN_IDS, DEBUG_MODE, LOG_LEVEL
from handlers.commands import (
    start_command, help_command, report_command, channels_command,
    segments_command, managers_command, update_command, forecast_command,
    alerts_command, test_metrika_command, channel_command, reserves_command,
    channels_chart_command, segments_chart_command, compare_channels_command,
    status_command
)
from handlers.schedule import setup_scheduler
from services.analytics import AnalyticsService
from utils.error_handler import error_handler

# Настройка логирования
log_level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=log_level,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

if DEBUG_MODE:
    logger.setLevel(logging.DEBUG)
    logger.debug("Debug mode enabled")

# Health check server
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            health_data = {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'service': 'telegram-analytics-bot'
            }
            self.wfile.write(json.dumps(health_data).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # Подавляем логи health check
        pass

def start_health_server():
    """Запуск HTTP сервера для health check"""
    try:
        server = HTTPServer(('0.0.0.0', 8000), HealthCheckHandler)
        logger.info("Health check server started on port 8000")
        server.serve_forever()
    except Exception as e:
        logger.error(f"Ошибка запуска health check сервера: {e}")

# Глобальный объект сервиса аналитики
analytics_service = None

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик ошибок"""
    logger.error(f"Exception while handling an update: {context.error}")
    
    # Отправка сообщения об ошибке администраторам
    if update and hasattr(update, 'effective_chat'):
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ Произошла ошибка при обработке команды. Администраторы уведомлены."
            )
        except Exception as e:
            logger.error(f"Failed to send error message: {e}")

def check_admin(func):
    """Декоратор для проверки прав администратора"""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id not in ADMIN_IDS:
            await update.message.reply_text("❌ У вас нет прав для выполнения этой команды.")
            return
        return await func(update, context)
    return wrapper

# Применяем декоратор к административным командам
update_command = check_admin(update_command)
forecast_command = check_admin(forecast_command)
test_metrika_command = check_admin(test_metrika_command)

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик неизвестных команд"""
    await update.message.reply_text(
        "❓ Неизвестная команда. Используйте /help для просмотра доступных команд."
    )

def main() -> None:
    """Основная функция запуска бота"""
    global analytics_service
    
    # Инициализация сервиса аналитики
    analytics_service = AnalyticsService()
    
    # Создание приложения
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрация обработчиков команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("report", report_command))
    application.add_handler(CommandHandler("channels", channels_command))
    application.add_handler(CommandHandler("channels_chart", channels_chart_command))
    application.add_handler(CommandHandler("segments", segments_command))
    application.add_handler(CommandHandler("segments_chart", segments_chart_command))
    application.add_handler(CommandHandler("managers", managers_command))
    application.add_handler(CommandHandler("update", update_command))
    application.add_handler(CommandHandler("forecast", forecast_command))
    application.add_handler(CommandHandler("compare", compare_channels_command))
    application.add_handler(CommandHandler("alerts", alerts_command))
    application.add_handler(CommandHandler("test_metrika", test_metrika_command))
    application.add_handler(CommandHandler("channel", channel_command))
    application.add_handler(CommandHandler("reserves", reserves_command))
    application.add_handler(CommandHandler("status", status_command))
    
    # Обработчик неизвестных команд
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    
    # Обработчик ошибок
    application.add_error_handler(error_handler)
    
    # Настройка планировщика задач
    setup_scheduler(application)
    
    # Запуск health check сервера в отдельном потоке
    health_thread = Thread(target=start_health_server, daemon=True)
    health_thread.start()
    
    logger.info("🚀 Telegram-бот 'Евгенич СПБ' запущен")
    
    # Запуск бота
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
