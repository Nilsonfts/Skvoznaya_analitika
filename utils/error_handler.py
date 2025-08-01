"""
Система обработки ошибок и логирования
"""

import logging
import traceback
from typing import Dict, Any, Optional
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

class ErrorHandler:
    """Централизованная система обработки ошибок"""
    
    def __init__(self):
        self.error_counts = {}
        self.last_errors = []
        self.max_last_errors = 50
    
    async def handle_error(self, update: Optional[Update], context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Основной обработчик ошибок для Telegram бота
        
        Args:
            update: Telegram Update объект
            context: Контекст выполнения
        """
        try:
            # Получаем информацию об ошибке
            error = context.error
            error_type = type(error).__name__
            error_message = str(error)
            
            # Увеличиваем счётчик ошибок
            self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
            
            # Записываем в список последних ошибок
            error_info = {
                'timestamp': datetime.now().isoformat(),
                'type': error_type,
                'message': error_message,
                'user_id': update.effective_user.id if update and update.effective_user else None,
                'chat_id': update.effective_chat.id if update and update.effective_chat else None,
                'update_type': update.update_id if update else None
            }
            
            self.last_errors.append(error_info)
            if len(self.last_errors) > self.max_last_errors:
                self.last_errors.pop(0)
            
            # Логируем ошибку
            logger.error(
                f"Error '{error_type}': {error_message}\n"
                f"User: {error_info.get('user_id', 'Unknown')}\n"
                f"Chat: {error_info.get('chat_id', 'Unknown')}\n"
                f"Traceback: {traceback.format_exc()}"
            )
            
            # Отправляем сообщение пользователю (если это не критическая ошибка)
            if update and update.effective_message:
                await self._send_user_error_message(update, error_type)
            
        except Exception as e:
            logger.critical(f"Ошибка в обработчике ошибок: {e}")
    
    async def _send_user_error_message(self, update: Update, error_type: str) -> None:
        """Отправка сообщения об ошибке пользователю"""
        try:
            # Определяем тип сообщения на основе типа ошибки
            if error_type in ['NetworkError', 'TimedOut', 'RetryAfter']:
                message = "🌐 Временные проблемы с сетью. Попробуйте позже."
            elif error_type in ['BadRequest', 'Unauthorized']:
                message = "❌ Неверный запрос. Проверьте команду и попробуйте снова."
            elif error_type in ['RateLimitError', 'FloodWait']:
                message = "⏰ Слишком много запросов. Подождите немного."
            elif error_type in ['DatabaseError', 'ConnectionError']:
                message = "🔧 Технические работы. Попробуйте позже."
            else:
                message = "❌ Произошла ошибка. Администратор уведомлён."
            
            await update.effective_message.reply_text(message)
            
        except Exception as e:
            logger.error(f"Не удалось отправить сообщение об ошибке: {e}")
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Получение статистики ошибок"""
        return {
            'error_counts': self.error_counts,
            'total_errors': sum(self.error_counts.values()),
            'unique_error_types': len(self.error_counts),
            'last_errors': self.last_errors[-10:],  # Последние 10 ошибок
            'most_common_error': max(self.error_counts.items(), key=lambda x: x[1]) if self.error_counts else None
        }
    
    def clear_error_stats(self) -> None:
        """Очистка статистики ошибок"""
        self.error_counts.clear()
        self.last_errors.clear()

# Глобальный экземпляр обработчика ошибок
_error_handler = None

def get_error_handler() -> ErrorHandler:
    """Получение экземпляра обработчика ошибок"""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler

async def error_handler(update: Optional[Update], context: ContextTypes.DEFAULT_TYPE) -> None:
    """Функция-обёртка для обработки ошибок"""
    handler = get_error_handler()
    await handler.handle_error(update, context)

# Декоратор для обработки ошибок в функциях
def handle_exceptions(func):
    """
    Декоратор для автоматической обработки исключений в командах
    
    Args:
        func: Функция для декорирования
        
    Returns:
        Обёрнутая функция с обработкой ошибок
    """
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        try:
            return await func(update, context, *args, **kwargs)
        except Exception as e:
            logger.error(f"Ошибка в команде {func.__name__}: {e}")
            
            # Отправляем сообщение об ошибке
            error_message = "❌ Произошла ошибка при выполнении команды. Попробуйте позже."
            
            if update and update.effective_message:
                try:
                    await update.effective_message.reply_text(error_message)
                except Exception as send_error:
                    logger.error(f"Не удалось отправить сообщение об ошибке: {send_error}")
            
            # Логируем ошибку в обработчик
            handler = get_error_handler()
            context.error = e
            await handler.handle_error(update, context)
    
    return wrapper

# Фильтры для типов ошибок
class ErrorFilters:
    """Фильтры для различных типов ошибок"""
    
    @staticmethod
    def is_network_error(error: Exception) -> bool:
        """Проверка на сетевую ошибку"""
        network_errors = ['NetworkError', 'TimedOut', 'ConnectionError', 'HTTPError']
        return type(error).__name__ in network_errors
    
    @staticmethod
    def is_user_error(error: Exception) -> bool:
        """Проверка на ошибку пользователя"""
        user_errors = ['BadRequest', 'InvalidFormat', 'ValueError']
        return type(error).__name__ in user_errors
    
    @staticmethod
    def is_rate_limit_error(error: Exception) -> bool:
        """Проверка на ошибку лимита запросов"""
        rate_errors = ['RateLimitError', 'FloodWait', 'RetryAfter']
        return type(error).__name__ in rate_errors
    
    @staticmethod
    def is_critical_error(error: Exception) -> bool:
        """Проверка на критическую ошибку"""
        critical_errors = ['DatabaseError', 'AuthenticationError', 'ConfigurationError']
        return type(error).__name__ in critical_errors

# Система метрик
class ErrorMetrics:
    """Система метрик для мониторинга ошибок"""
    
    def __init__(self):
        self.metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'error_rate': 0.0,
            'uptime_start': datetime.now()
        }
    
    def record_request(self, success: bool = True) -> None:
        """Записать запрос в метрики"""
        self.metrics['total_requests'] += 1
        
        if success:
            self.metrics['successful_requests'] += 1
        else:
            self.metrics['failed_requests'] += 1
        
        # Обновляем процент ошибок
        if self.metrics['total_requests'] > 0:
            self.metrics['error_rate'] = (
                self.metrics['failed_requests'] / self.metrics['total_requests'] * 100
            )
    
    def get_uptime(self) -> str:
        """Получить время работы"""
        uptime_delta = datetime.now() - self.metrics['uptime_start']
        days = uptime_delta.days
        hours, remainder = divmod(uptime_delta.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        
        return f"{days}д {hours}ч {minutes}м"
    
    def get_metrics(self) -> Dict[str, Any]:
        """Получить все метрики"""
        return {
            **self.metrics,
            'uptime': self.get_uptime()
        }
    
    def reset_metrics(self) -> None:
        """Сброс метрик"""
        self.metrics.update({
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'error_rate': 0.0,
            'uptime_start': datetime.now()
        })

# Глобальные экземпляры
_metrics = ErrorMetrics()

def get_metrics() -> ErrorMetrics:
    """Получение экземпляра метрик"""
    global _metrics
    return _metrics
