"""
Сервис для работы с API Яндекс.Метрики
"""

import logging
import aiohttp
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json

from config import METRIKA_COUNTER_ID, METRIKA_OAUTH_TOKEN, METRIKA_API_CONFIG

logger = logging.getLogger(__name__)

class MetrikaService:
    def __init__(self):
        """Инициализация сервиса Яндекс.Метрики"""
        self.counter_id = METRIKA_COUNTER_ID
        self.oauth_token = METRIKA_OAUTH_TOKEN
        self.base_url = METRIKA_API_CONFIG['base_url']
        self.batch_size = METRIKA_API_CONFIG['batch_size']
        self.request_delay = METRIKA_API_CONFIG['request_delay']
        self.metrics = METRIKA_API_CONFIG['metrics']
        
        # Заголовки для запросов
        self.headers = {
            'Authorization': f'OAuth {self.oauth_token}',
            'Content-Type': 'application/json'
        }
        
        logger.info("Сервис Яндекс.Метрики инициализирован")
    
    async def test_connection(self) -> Dict[str, Any]:
        """Тестирование соединения с API"""
        try:
            start_time = datetime.now()
            
            # Получаем данные за вчера для проверки
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/stat/v1/data"
                params = {
                    'id': self.counter_id,
                    'date1': yesterday,
                    'date2': yesterday,
                    'metrics': 'ym:s:visits',
                    'accuracy': 'full'
                }
                
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        visits = data.get('data', [{}])[0].get('metrics', [0])[0] if data.get('data') else 0
                        
                        response_time = int((datetime.now() - start_time).total_seconds() * 1000)
                        
                        return {
                            'success': True,
                            'counter_id': self.counter_id,
                            'yesterday_visits': visits,
                            'response_time': response_time
                        }
                    else:
                        error_text = await response.text()
                        return {
                            'success': False,
                            'error': f"HTTP {response.status}: {error_text}"
                        }
                        
        except Exception as e:
            logger.error(f"Ошибка тестирования соединения с Метрикой: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_client_metrics(self, client_id: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """Получение метрик для конкретного клиента"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/stat/v1/data"
                params = {
                    'id': self.counter_id,
                    'date1': start_date,
                    'date2': end_date,
                    'metrics': ','.join(self.metrics),
                    'filters': f'ym:s:clientID==\'{client_id}\'',
                    'accuracy': 'full'
                }
                
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get('data') and len(data['data']) > 0:
                            metrics_data = data['data'][0]['metrics']
                            
                            return {
                                'visits': int(metrics_data[0]) if len(metrics_data) > 0 else 0,
                                'pageviews': int(metrics_data[1]) if len(metrics_data) > 1 else 0,
                                'bounce_rate': float(metrics_data[2]) if len(metrics_data) > 2 else 0.0,
                                'avg_visit_duration': int(metrics_data[3]) if len(metrics_data) > 3 else 0
                            }
                        else:
                            # Нет данных для клиента
                            return {
                                'visits': 0,
                                'pageviews': 0,
                                'bounce_rate': 0.0,
                                'avg_visit_duration': 0
                            }
                    else:
                        logger.warning(f"Ошибка получения данных для клиента {client_id}: HTTP {response.status}")
                        return {
                            'visits': 0,
                            'pageviews': 0,
                            'bounce_rate': 0.0,
                            'avg_visit_duration': 0
                        }
                        
        except Exception as e:
            logger.error(f"Ошибка получения метрик для клиента {client_id}: {e}")
            return {
                'visits': 0,
                'pageviews': 0,
                'bounce_rate': 0.0,
                'avg_visit_duration': 0
            }
    
    async def get_batch_client_metrics(self, leads: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Получение метрик для батча лидов"""
        results = {}
        
        # Фильтруем лиды с корректными YM Client ID
        valid_leads = []
        for lead in leads:
            client_id = lead.get('ym_client_id', '').strip()
            if client_id and client_id != '' and lead.get('date'):
                valid_leads.append(lead)
        
        if not valid_leads:
            logger.info("Нет лидов с корректными YM Client ID")
            return results
        
        # Обрабатываем батчами
        for i in range(0, len(valid_leads), self.batch_size):
            batch = valid_leads[i:i + self.batch_size]
            
            # Создаем задачи для параллельного выполнения
            tasks = []
            for lead in batch:
                client_id = lead['ym_client_id']
                lead_date = self._parse_date(lead['date'])
                
                if lead_date:
                    # Период: 30 дней до заявки
                    start_date = (lead_date - timedelta(days=30)).strftime('%Y-%m-%d')
                    end_date = lead_date.strftime('%Y-%m-%d')
                    
                    task = self.get_client_metrics(client_id, start_date, end_date)
                    tasks.append((client_id, task))
            
            # Выполняем запросы параллельно
            if tasks:
                task_results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
                
                # Сохраняем результаты
                for (client_id, _), result in zip(tasks, task_results):
                    if isinstance(result, Exception):
                        logger.error(f"Ошибка для клиента {client_id}: {result}")
                        results[client_id] = {
                            'visits': 0,
                            'pageviews': 0,
                            'bounce_rate': 0.0,
                            'avg_visit_duration': 0
                        }
                    else:
                        results[client_id] = result
                
                # Пауза между батчами для соблюдения лимитов API
                if i + self.batch_size < len(valid_leads):
                    await asyncio.sleep(self.request_delay)
        
        logger.info(f"Получены метрики для {len(results)} клиентов")
        return results
    
    async def get_channel_metrics(self, channel: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """Получение агрегированных метрик по каналу"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/stat/v1/data"
                
                # Формируем фильтр на основе канала
                channel_filter = self._get_channel_filter(channel)
                
                params = {
                    'id': self.counter_id,
                    'date1': start_date,
                    'date2': end_date,
                    'metrics': ','.join(self.metrics),
                    'group': 'all',
                    'accuracy': 'full'
                }
                
                if channel_filter:
                    params['filters'] = channel_filter
                
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get('data') and len(data['data']) > 0:
                            metrics_data = data['data'][0]['metrics']
                            
                            return {
                                'visits': int(metrics_data[0]) if len(metrics_data) > 0 else 0,
                                'pageviews': int(metrics_data[1]) if len(metrics_data) > 1 else 0,
                                'bounce_rate': float(metrics_data[2]) if len(metrics_data) > 2 else 0.0,
                                'avg_visit_duration': int(metrics_data[3]) if len(metrics_data) > 3 else 0,
                                'engagement_rate': self._calculate_engagement_rate(metrics_data)
                            }
                        else:
                            return {
                                'visits': 0,
                                'pageviews': 0,
                                'bounce_rate': 0.0,
                                'avg_visit_duration': 0,
                                'engagement_rate': 0.0
                            }
                    else:
                        logger.warning(f"Ошибка получения данных для канала {channel}: HTTP {response.status}")
                        return {
                            'visits': 0,
                            'pageviews': 0,
                            'bounce_rate': 0.0,
                            'avg_visit_duration': 0,
                            'engagement_rate': 0.0
                        }
                        
        except Exception as e:
            logger.error(f"Ошибка получения метрик для канала {channel}: {e}")
            return {
                'visits': 0,
                'pageviews': 0,
                'bounce_rate': 0.0,
                'avg_visit_duration': 0,
                'engagement_rate': 0.0
            }
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Парсинг даты из различных форматов"""
        if not date_str:
            return None
        
        # Список возможных форматов даты
        date_formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d',
            '%d.%m.%Y %H:%M:%S',
            '%d.%m.%Y',
            '%d/%m/%Y %H:%M:%S',
            '%d/%m/%Y'
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue
        
        logger.warning(f"Не удалось распарсить дату: {date_str}")
        return None
    
    def _get_channel_filter(self, channel: str) -> str:
        """Формирование фильтра для канала в запросе к Метрике"""
        # Маппинг каналов на источники трафика в Метрике
        channel_mapping = {
            'Yandex': 'ym:s:searchEngine==\'yandex\'',
            'Google': 'ym:s:searchEngine==\'google\'',
            'Instagram': 'ym:s:socialNetwork==\'instagram\'',
            'Facebook': 'ym:s:socialNetwork==\'facebook\'',
            'VKontakte': 'ym:s:socialNetwork==\'vkontakte\'',
            'Telegram': 'ym:s:socialNetwork==\'telegram\'',
            'Direct': 'ym:s:trafficSource==\'direct\'',
            '2GIS': 'ym:s:referrer=@\'2gis\'',
            'Yandex Maps': 'ym:s:referrer=@\'maps.yandex\''
        }
        
        return channel_mapping.get(channel, '')
    
    def _calculate_engagement_rate(self, metrics_data: List) -> float:
        """Расчет индекса вовлеченности"""
        try:
            if len(metrics_data) < 4:
                return 0.0
            
            visits = int(metrics_data[0]) if metrics_data[0] else 0
            pageviews = int(metrics_data[1]) if metrics_data[1] else 0
            bounce_rate = float(metrics_data[2]) if metrics_data[2] else 0.0
            avg_duration = int(metrics_data[3]) if metrics_data[3] else 0
            
            if visits == 0:
                return 0.0
            
            # Формула индекса вовлеченности
            pages_per_visit = pageviews / visits if visits > 0 else 0
            engagement_rate = (
                (1 - bounce_rate / 100) * 0.4 +  # Низкий показатель отказов
                min(pages_per_visit / 3, 1) * 0.3 +  # Количество страниц за визит
                min(avg_duration / 180, 1) * 0.3  # Время на сайте (нормализовано к 3 минутам)
            ) * 100
            
            return round(engagement_rate, 2)
            
        except Exception as e:
            logger.error(f"Ошибка расчета индекса вовлеченности: {e}")
            return 0.0
    
    async def get_top_pages(self, start_date: str, end_date: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Получение топ страниц по просмотрам"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/stat/v1/data"
                params = {
                    'id': self.counter_id,
                    'date1': start_date,
                    'date2': end_date,
                    'metrics': 'ym:pv:pageviews,ym:pv:users',
                    'dimensions': 'ym:pv:URLPath',
                    'sort': '-ym:pv:pageviews',
                    'limit': limit,
                    'accuracy': 'full'
                }
                
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        pages = []
                        
                        for item in data.get('data', []):
                            pages.append({
                                'url': item['dimensions'][0]['name'],
                                'pageviews': item['metrics'][0],
                                'users': item['metrics'][1]
                            })
                        
                        return pages
                    else:
                        logger.warning(f"Ошибка получения топ страниц: HTTP {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Ошибка получения топ страниц: {e}")
            return []
