"""
Rate Limiting middleware для защиты от флуда
"""

import time
import logging
from functools import wraps
from typing import Dict, Optional
from telegram import Update
from telegram.ext import ContextTypes
from services.cache import CacheService
from config import RATE_LIMIT_PER_MINUTE, EMOJI

logger = logging.getLogger(__name__)

class RateLimiter:
    """Класс для ограничения частоты запросов"""
    
    def __init__(self, cache_service: Optional[CacheService] = None):
        self.cache = cache_service or CacheService()
        self.rate_limit = RATE_LIMIT_PER_MINUTE
        
    async def is_rate_limited(self, user_id: int) -> bool:
        """
        Проверка, превышен ли лимит запросов для пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            True если лимит превышен, False если нет
        """
        try:
            current_time = int(time.time())
            minute_window = current_time // 60  # Окно в 1 минуту
            
            key = f"rate_limit:{user_id}:{minute_window}"
            
            # Получаем текущее количество запросов
            current_requests = await self.cache.get(key)
            
            if current_requests is None:
                # Первый запрос в этом окне
                await self.cache.set(key, 1, expire=70)  # TTL чуть больше минуты
                return False
            
            current_count = int(current_requests)
            
            if current_count >= self.rate_limit:
                return True
            
            # Увеличиваем счётчик
            await self.cache.increment(key)
            return False
            
        except Exception as e:
            logger.error(f"Ошибка в rate limiter: {e}")
            # В случае ошибки не блокируем пользователя
            return False
    
    async def get_remaining_requests(self, user_id: int) -> int:
        """
        Получение количества оставшихся запросов
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Количество оставшихся запросов
        """
        try:
            current_time = int(time.time())
            minute_window = current_time // 60
            key = f"rate_limit:{user_id}:{minute_window}"
            
            current_requests = await self.cache.get(key)
            
            if current_requests is None:
                return self.rate_limit
            
            used_requests = int(current_requests)
            return max(0, self.rate_limit - used_requests)
            
        except Exception as e:
            logger.error(f"Ошибка получения оставшихся запросов: {e}")
            return self.rate_limit
    
    async def get_time_until_reset(self, user_id: int) -> int:
        """
        Получение времени до сброса лимита в секундах
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Секунды до сброса лимита
        """
        current_time = int(time.time())
        seconds_in_current_minute = current_time % 60
        return 60 - seconds_in_current_minute

# Глобальный экземпляр rate limiter
rate_limiter = RateLimiter()

def rate_limit(func):
    """
    Декоратор для применения rate limiting к командам бота
    
    Args:
        func: Функция-обработчик команды
        
    Returns:
        Обёрнутая функция с проверкой rate limit
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        
        # Проверяем rate limit
        if await rate_limiter.is_rate_limited(user_id):
            # Получаем информацию для пользователя
            remaining_time = await rate_limiter.get_time_until_reset(user_id)
            
            limit_message = f"""
{EMOJI['warning']} **Превышен лимит запросов**

Вы отправили слишком много команд. Максимум **{RATE_LIMIT_PER_MINUTE} команд в минуту**.

⏰ Попробуйте снова через **{remaining_time} секунд**.

💡 Это ограничение защищает бота от перегрузки и обеспечивает стабильную работу для всех пользователей.
"""
            
            await update.message.reply_text(limit_message, parse_mode='Markdown')
            
            # Логируем превышение лимита
            logger.warning(f"Rate limit exceeded for user {user_id} (@{update.effective_user.username})")
            
            return
        
        # Если лимит не превышен, выполняем команду
        await func(update, context)
    
    return wrapper

def admin_rate_limit(func):
    """
    Декоратор с более мягким rate limiting для администраторов
    
    Args:
        func: Функция-обработчик команды
        
    Returns:
        Обёрнутая функция с проверкой rate limit для админов
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        from config import ADMIN_IDS
        
        user_id = update.effective_user.id
        
        # Для админов увеличиваем лимит в 3 раза
        admin_limiter = RateLimiter()
        admin_limiter.rate_limit = RATE_LIMIT_PER_MINUTE * 3
        
        if user_id in ADMIN_IDS:
            if await admin_limiter.is_rate_limited(user_id):
                remaining_time = await admin_limiter.get_time_until_reset(user_id)
                
                limit_message = f"""
{EMOJI['warning']} **Превышен лимит запросов (админ)**

Максимум **{admin_limiter.rate_limit} команд в минуту**.

⏰ Попробуйте снова через **{remaining_time} секунд**.
"""
                
                await update.message.reply_text(limit_message, parse_mode='Markdown')
                return
        else:
            # Для обычных пользователей используем стандартный лимит
            if await rate_limiter.is_rate_limited(user_id):
                remaining_time = await rate_limiter.get_time_until_reset(user_id)
                
                limit_message = f"""
{EMOJI['warning']} **Превышен лимит запросов**

Максимум **{RATE_LIMIT_PER_MINUTE} команд в минуту**.

⏰ Попробуйте снова через **{remaining_time} секунд**.
"""
                
                await update.message.reply_text(limit_message, parse_mode='Markdown')
                return
        
        # Выполняем команду
        await func(update, context)
    
    return wrapper

async def get_rate_limit_stats(user_id: int) -> Dict[str, int]:
    """
    Получение статистики rate limit для пользователя
    
    Args:
        user_id: ID пользователя
        
    Returns:
        Словарь со статистикой
    """
    remaining = await rate_limiter.get_remaining_requests(user_id)
    reset_time = await rate_limiter.get_time_until_reset(user_id)
    
    return {
        'limit': RATE_LIMIT_PER_MINUTE,
        'remaining': remaining,
        'used': RATE_LIMIT_PER_MINUTE - remaining,
        'reset_in_seconds': reset_time
    }
