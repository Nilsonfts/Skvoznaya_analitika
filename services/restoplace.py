"""
Сервис для работы с API RestoPlace
"""

import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from config import RESTOPLACE_API_KEY

logger = logging.getLogger(__name__)

class RestoPlaceService:
    """Сервис для работы с API RestoPlace"""
    
    BASE_URL = "https://api.restoplace.cc"
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or RESTOPLACE_API_KEY
        self.session = None
    
    async def __aenter__(self):
        """Создание async context manager"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Закрытие async context manager"""
        if self.session:
            await self.session.close()
    
    async def get_reserves(self, updated_after_time: Optional[str] = None, 
                          page: int = 1, page_size: int = 100) -> Dict:
        """
        Получение резервов из API RestoPlace
        
        Args:
            updated_after_time: Timestamp для получения только обновлённых записей
            page: Номер страницы
            page_size: Размер страницы
        
        Returns:
            Словарь с данными резервов
        """
        if not self.api_key:
            raise ValueError("RestoPlace API key not configured")
        
        params = {
            'api_key': self.api_key,
            'page': page,
            'limit': page_size
        }
        
        if updated_after_time:
            params['updatedAfterTime'] = updated_after_time
        
        try:
            url = f"{self.BASE_URL}/reserves"
            logger.info(f"Запрос к RestoPlace API: page={page}, updated_after={updated_after_time}")
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Получено {len(data.get('data', []))} резервов со страницы {page}")
                    return data
                else:
                    logger.error(f"Ошибка API RestoPlace: {response.status}")
                    response_text = await response.text()
                    logger.error(f"Ответ сервера: {response_text}")
                    raise Exception(f"RestoPlace API error: {response.status}")
                    
        except Exception as e:
            logger.error(f"Ошибка при запросе к RestoPlace API: {e}")
            raise
    
    async def get_all_reserves(self, days_back: int = 45) -> List[Dict]:
        """
        Получение всех резервов за указанный период
        
        Args:
            days_back: Количество дней назад для получения данных
        
        Returns:
            Список всех резервов
        """
        # Вычисляем timestamp для фильтрации
        start_date = datetime.now() - timedelta(days=days_back)
        updated_after_time = start_date.strftime('%Y-%m-%d %H:%M:%S')
        
        all_reserves = []
        page = 1
        
        while True:
            try:
                data = await self.get_reserves(
                    updated_after_time=updated_after_time,
                    page=page
                )
                
                reserves = data.get('data', [])
                if not reserves:
                    break
                
                all_reserves.extend(reserves)
                
                # Проверяем, есть ли ещё страницы
                pagination = data.get('pagination', {})
                current_page = pagination.get('current_page', page)
                total_pages = pagination.get('total_pages', page)
                
                if current_page >= total_pages:
                    break
                
                page += 1
                
                # Небольшая задержка между запросами
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Ошибка при получении страницы {page}: {e}")
                break
        
        logger.info(f"Всего получено {len(all_reserves)} резервов за {days_back} дней")
        return all_reserves
    
    def format_reserve_data(self, reserve: Dict) -> Dict:
        """
        Форматирование данных резерва для записи в Google Sheets
        
        Args:
            reserve: Данные резерва из API
        
        Returns:
            Отформатированные данные
        """
        return {
            'id': reserve.get('id', ''),
            'reserve_id': reserve.get('reserve_id', ''),
            'name': reserve.get('name', ''),
            'phone': self._format_phone(reserve.get('phone', '')),
            'email': reserve.get('email', ''),
            'time_from': self._format_datetime(reserve.get('time_from', '')),
            'status': reserve.get('status', ''),
            'order_sum': float(reserve.get('order_sum', 0)),
            'count': int(reserve.get('count', 0)),
            'source': reserve.get('source', ''),
            'created_at': self._format_datetime(reserve.get('created_at', '')),
            'updated_at': self._format_datetime(reserve.get('updated_at', ''))
        }
    
    def _format_phone(self, phone: str) -> str:
        """Форматирование номера телефона"""
        if not phone:
            return ''
        
        # Убираем все нецифровые символы
        digits = ''.join(filter(str.isdigit, phone))
        
        # Если номер начинается с 8, заменяем на +7
        if digits.startswith('8') and len(digits) == 11:
            digits = '7' + digits[1:]
        
        # Добавляем + если его нет
        if digits.startswith('7') and len(digits) == 11:
            return '+' + digits
        
        return phone
    
    def _format_datetime(self, dt_string: str) -> str:
        """Форматирование даты и времени"""
        if not dt_string:
            return ''
        
        try:
            # Пробуем разные форматы даты
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%dT%H:%M:%SZ',
                '%Y-%m-%d'
            ]
            
            for fmt in formats:
                try:
                    dt = datetime.strptime(dt_string, fmt)
                    return dt.strftime('%Y-%m-%d %H:%M:%S')
                except ValueError:
                    continue
            
            return dt_string
            
        except Exception as e:
            logger.warning(f"Ошибка форматирования даты {dt_string}: {e}")
            return dt_string
    
    def aggregate_guests_data(self, reserves: List[Dict]) -> List[Dict]:
        """
        Агрегация данных по гостям
        
        Args:
            reserves: Список резервов
        
        Returns:
            Список агрегированных данных по гостям
        """
        guests_data = {}
        
        for reserve in reserves:
            phone = reserve.get('phone', '')
            if not phone:
                continue
            
            # Используем телефон как ключ для группировки
            if phone not in guests_data:
                guests_data[phone] = {
                    'name': reserve.get('name', ''),
                    'phone': phone,
                    'email': reserve.get('email', ''),
                    'visits': [],
                    'total_sum': 0,
                    'visits_count': 0,
                    'first_visit': None,
                    'last_visit': None
                }
            
            guest = guests_data[phone]
            
            # Обновляем имя и email если они пустые
            if not guest['name'] and reserve.get('name'):
                guest['name'] = reserve.get('name')
            if not guest['email'] and reserve.get('email'):
                guest['email'] = reserve.get('email')
            
            # Добавляем визит
            visit_date = reserve.get('time_from', '')
            visit_sum = float(reserve.get('order_sum', 0))
            
            if visit_date and visit_sum > 0:
                # Проверяем на дубли (одинаковая дата и сумма)
                visit_key = f"{visit_date}_{visit_sum}"
                existing_visits = [f"{v['date']}_{v['sum']}" for v in guest['visits']]
                
                if visit_key not in existing_visits:
                    guest['visits'].append({
                        'date': visit_date,
                        'sum': visit_sum,
                        'status': reserve.get('status', ''),
                        'count': reserve.get('count', 1)
                    })
                    
                    guest['total_sum'] += visit_sum
                    guest['visits_count'] += 1
                    
                    # Обновляем первый и последний визит
                    visit_dt = self._parse_datetime(visit_date)
                    if visit_dt:
                        if not guest['first_visit'] or visit_dt < self._parse_datetime(guest['first_visit']):
                            guest['first_visit'] = visit_date
                        if not guest['last_visit'] or visit_dt > self._parse_datetime(guest['last_visit']):
                            guest['last_visit'] = visit_date
        
        # Сортируем визиты по дате (новые сначала) и берём последние 10
        for guest in guests_data.values():
            guest['visits'].sort(key=lambda x: self._parse_datetime(x['date']) or datetime.min, reverse=True)
            guest['visits'] = guest['visits'][:10]  # Оставляем только 10 последних визитов
        
        return list(guests_data.values())
    
    def _parse_datetime(self, dt_string: str) -> Optional[datetime]:
        """Парсинг даты из строки"""
        if not dt_string:
            return None
        
        try:
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%dT%H:%M:%SZ',
                '%Y-%m-%d'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(dt_string, fmt)
                except ValueError:
                    continue
            
            return None
            
        except Exception:
            return None
