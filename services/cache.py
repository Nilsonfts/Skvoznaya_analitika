"""
Сервис кеширования данных с использованием Redis
"""

import logging
import redis
import json
import pickle
from typing import Any, Optional, Union
from datetime import datetime, timedelta
from urllib.parse import urlparse
import os

logger = logging.getLogger(__name__)

class CacheService:
    def __init__(self):
        """Инициализация сервиса кеширования"""
        try:
            # Попытка подключения к Redis
            redis_url = os.getenv('REDIS_URL')
            
            if redis_url:
                # Подключение через URL (Railway)
                self.redis_client = redis.from_url(redis_url, decode_responses=False)
            else:
                # Подключение через отдельные параметры
                from config import REDIS_CONFIG
                self.redis_client = redis.Redis(
                    host=REDIS_CONFIG['host'],
                    port=REDIS_CONFIG['port'],
                    db=REDIS_CONFIG['db'],
                    password=REDIS_CONFIG['password'],
                    decode_responses=False  # Для работы с pickle
                )
            
            # Проверка подключения
            self.redis_client.ping()
            self.available = True
            logger.info("Redis подключен успешно")
            
        except Exception as e:
            logger.warning(f"Redis недоступен, кеширование отключено: {e}")
            self.redis_client = None
            self.available = False
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """
        Сохранение значения в кеш
        
        Args:
            key: Ключ для сохранения
            value: Значение для сохранения
            ttl: Время жизни в секундах (по умолчанию 1 час)
        
        Returns:
            True если успешно сохранено
        """
        if not self.available:
            return False
        
        try:
            # Сериализация значения
            serialized_value = pickle.dumps(value)
            
            # Сохранение с TTL
            result = self.redis_client.setex(key, ttl, serialized_value)
            
            logger.debug(f"Кеш сохранен: {key} (TTL: {ttl}s)")
            return bool(result)
            
        except Exception as e:
            logger.error(f"Ошибка сохранения в кеш {key}: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """
        Получение значения из кеша
        
        Args:
            key: Ключ для получения
        
        Returns:
            Значение из кеша или None
        """
        if not self.available:
            return None
        
        try:
            serialized_value = self.redis_client.get(key)
            
            if serialized_value is None:
                logger.debug(f"Кеш промах: {key}")
                return None
            
            # Десериализация значения
            value = pickle.loads(serialized_value)
            
            logger.debug(f"Кеш попадание: {key}")
            return value
            
        except Exception as e:
            logger.error(f"Ошибка получения из кеша {key}: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """
        Удаление значения из кеша
        
        Args:
            key: Ключ для удаления
        
        Returns:
            True если успешно удалено
        """
        if not self.available:
            return False
        
        try:
            result = self.redis_client.delete(key)
            logger.debug(f"Кеш удален: {key}")
            return bool(result)
            
        except Exception as e:
            logger.error(f"Ошибка удаления из кеша {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """
        Проверка существования ключа в кеше
        
        Args:
            key: Ключ для проверки
        
        Returns:
            True если ключ существует
        """
        if not self.available:
            return False
        
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Ошибка проверки существования ключа {key}: {e}")
            return False
    
    def set_json(self, key: str, value: dict, ttl: int = 3600) -> bool:
        """
        Сохранение JSON данных в кеш
        
        Args:
            key: Ключ для сохранения
            value: Словарь для сохранения
            ttl: Время жизни в секундах
        
        Returns:
            True если успешно сохранено
        """
        if not self.available:
            return False
        
        try:
            json_value = json.dumps(value, ensure_ascii=False, default=str)
            result = self.redis_client.setex(f"json:{key}", ttl, json_value)
            
            logger.debug(f"JSON кеш сохранен: {key}")
            return bool(result)
            
        except Exception as e:
            logger.error(f"Ошибка сохранения JSON в кеш {key}: {e}")
            return False
    
    def get_json(self, key: str) -> Optional[dict]:
        """
        Получение JSON данных из кеша
        
        Args:
            key: Ключ для получения
        
        Returns:
            Словарь из кеша или None
        """
        if not self.available:
            return None
        
        try:
            json_value = self.redis_client.get(f"json:{key}")
            
            if json_value is None:
                return None
            
            value = json.loads(json_value.decode('utf-8'))
            logger.debug(f"JSON кеш попадание: {key}")
            return value
            
        except Exception as e:
            logger.error(f"Ошибка получения JSON из кеша {key}: {e}")
            return None
    
    def increment(self, key: str, amount: int = 1, ttl: int = 3600) -> Optional[int]:
        """
        Инкремент значения счетчика
        
        Args:
            key: Ключ счетчика
            amount: Значение для увеличения
            ttl: Время жизни для нового ключа
        
        Returns:
            Новое значение счетчика
        """
        if not self.available:
            return None
        
        try:
            # Если ключ не существует, создаем его с TTL
            if not self.exists(key):
                self.redis_client.setex(key, ttl, 0)
            
            result = self.redis_client.incrby(key, amount)
            logger.debug(f"Счетчик увеличен: {key} = {result}")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка инкремента счетчика {key}: {e}")
            return None
    
    def get_keys_pattern(self, pattern: str) -> list:
        """
        Получение ключей по шаблону
        
        Args:
            pattern: Шаблон для поиска (например, "user:*")
        
        Returns:
            Список найденных ключей
        """
        if not self.available:
            return []
        
        try:
            keys = self.redis_client.keys(pattern)
            decoded_keys = [key.decode('utf-8') if isinstance(key, bytes) else key for key in keys]
            return decoded_keys
            
        except Exception as e:
            logger.error(f"Ошибка поиска ключей по шаблону {pattern}: {e}")
            return []
    
    def clear_pattern(self, pattern: str) -> int:
        """
        Удаление всех ключей по шаблону
        
        Args:
            pattern: Шаблон для удаления
        
        Returns:
            Количество удаленных ключей
        """
        if not self.available:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                result = self.redis_client.delete(*keys)
                logger.info(f"Удалено {result} ключей по шаблону {pattern}")
                return result
            return 0
            
        except Exception as e:
            logger.error(f"Ошибка удаления ключей по шаблону {pattern}: {e}")
            return 0
    
    def get_ttl(self, key: str) -> int:
        """
        Получение времени жизни ключа
        
        Args:
            key: Ключ для проверки
        
        Returns:
            Время жизни в секундах (-1 если ключ не истекает, -2 если не существует)
        """
        if not self.available:
            return -2
        
        try:
            return self.redis_client.ttl(key)
        except Exception as e:
            logger.error(f"Ошибка получения TTL для ключа {key}: {e}")
            return -2
    
    def extend_ttl(self, key: str, ttl: int) -> bool:
        """
        Продление времени жизни ключа
        
        Args:
            key: Ключ для продления
            ttl: Новое время жизни в секундах
        
        Returns:
            True если успешно продлено
        """
        if not self.available:
            return False
        
        try:
            result = self.redis_client.expire(key, ttl)
            return bool(result)
        except Exception as e:
            logger.error(f"Ошибка продления TTL для ключа {key}: {e}")
            return False
    
    def get_info(self) -> dict:
        """
        Получение информации о Redis сервере
        
        Returns:
            Словарь с информацией о сервере
        """
        if not self.available:
            return {'available': False}
        
        try:
            info = self.redis_client.info()
            return {
                'available': True,
                'redis_version': info.get('redis_version'),
                'used_memory_human': info.get('used_memory_human'),
                'connected_clients': info.get('connected_clients'),
                'total_commands_processed': info.get('total_commands_processed'),
                'keyspace': info.get('db0', {})
            }
        except Exception as e:
            logger.error(f"Ошибка получения информации о Redis: {e}")
            return {'available': False, 'error': str(e)}
    
    def flush_all(self) -> bool:
        """
        Очистка всего кеша (используйте с осторожностью!)
        
        Returns:
            True если успешно очищено
        """
        if not self.available:
            return False
        
        try:
            self.redis_client.flushdb()
            logger.warning("Весь кеш очищен!")
            return True
        except Exception as e:
            logger.error(f"Ошибка очистки кеша: {e}")
            return False

# Глобальный экземпляр сервиса кеширования
cache_service = CacheService()

def cache_result(key_prefix: str, ttl: int = 3600):
    """
    Декоратор для кеширования результатов функций
    
    Args:
        key_prefix: Префикс для ключа кеша
        ttl: Время жизни кеша в секундах
    
    Usage:
        @cache_result("user_data", ttl=1800)
        def get_user_data(user_id):
            # Тяжелая операция
            return data
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Формирование ключа кеша
            cache_key = f"{key_prefix}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # Попытка получить из кеша
            cached_result = cache_service.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Результат получен из кеша: {func.__name__}")
                return cached_result
            
            # Выполнение функции и кеширование результата
            result = func(*args, **kwargs)
            cache_service.set(cache_key, result, ttl)
            
            logger.debug(f"Результат сохранен в кеш: {func.__name__}")
            return result
        
        return wrapper
    return decorator
