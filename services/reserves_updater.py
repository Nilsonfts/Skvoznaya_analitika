"""
Сервис для обновления данных резервов из RestoPlace
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Tuple
from services.restoplace import RestoPlaceService
from services.google_sheets import GoogleSheetsService

logger = logging.getLogger(__name__)

class ReservesUpdateService:
    """Сервис для обновления данных резервов"""
    
    def __init__(self):
        self.sheets_service = GoogleSheetsService()
        
    async def update_reserves_data(self, days_back: int = 45) -> Dict[str, int]:
        """
        Полное обновление данных резервов
        
        Args:
            days_back: Количество дней для получения данных
            
        Returns:
            Статистика обновления
        """
        try:
            logger.info("Начинаем обновление данных резервов из RestoPlace")
            
            # 1. Получаем данные из RestoPlace API
            async with RestoPlaceService() as rp_service:
                fresh_reserves = await rp_service.get_all_reserves(days_back=days_back)
            
            if not fresh_reserves:
                logger.warning("Не получено данных из RestoPlace API")
                return {
                    'reserves_updated': 0,
                    'guests_updated': 0,
                    'error': 'Нет данных из API'
                }
            
            # 2. Получаем исторические данные из листа "Выгрузка РП"
            historical_data = self._get_historical_data()
            
            # 3. Объединяем данные
            all_reserves = self._merge_reserves_data(fresh_reserves, historical_data)
            
            # 4. Обновляем лист "Reserves RP"
            reserves_updated = await self._update_reserves_sheet(all_reserves)
            
            # 5. Агрегируем данные по гостям
            async with RestoPlaceService() as rp_service:
                guests_data = rp_service.aggregate_guests_data(all_reserves)
            
            # 6. Обновляем лист "Guests RP"
            guests_updated = await self._update_guests_sheet(guests_data)
            
            logger.info(f"Обновление завершено: {reserves_updated} резервов, {guests_updated} гостей")
            
            return {
                'reserves_updated': reserves_updated,
                'guests_updated': guests_updated,
                'total_reserves': len(all_reserves),
                'api_reserves': len(fresh_reserves),
                'historical_reserves': len(historical_data)
            }
            
        except Exception as e:
            logger.error(f"Ошибка при обновлении данных резервов: {e}")
            return {
                'reserves_updated': 0,
                'guests_updated': 0,
                'error': str(e)
            }
    
    def _get_historical_data(self) -> List[Dict]:
        """Получение исторических данных из листа 'Выгрузка РП'"""
        try:
            data = self.sheets_service.read_sheet("Выгрузка РП")
            if not data or len(data) < 2:
                logger.info("Нет исторических данных в листе 'Выгрузка РП'")
                return []
            
            headers = data[0]
            historical_reserves = []
            
            for row in data[1:]:
                if len(row) >= len(headers):
                    reserve = {}
                    for i, header in enumerate(headers):
                        reserve[header.lower().replace(' ', '_')] = row[i] if i < len(row) else ''
                    historical_reserves.append(reserve)
            
            logger.info(f"Получено {len(historical_reserves)} исторических записей")
            return historical_reserves
            
        except Exception as e:
            logger.error(f"Ошибка при получении исторических данных: {e}")
            return []
    
    def _merge_reserves_data(self, fresh_reserves: List[Dict], 
                           historical_data: List[Dict]) -> List[Dict]:
        """
        Объединение свежих данных с историческими
        
        Args:
            fresh_reserves: Данные из API RestoPlace
            historical_data: Исторические данные
            
        Returns:
            Объединённый список резервов
        """
        # Создаём множество ID свежих резервов для быстрого поиска
        # Форматируем свежие данные без async context (данные уже получены)
        rp_service = RestoPlaceService()
        formatted_fresh = [rp_service.format_reserve_data(reserve) for reserve in fresh_reserves]
        
        fresh_ids = {str(reserve.get('id', '')) for reserve in formatted_fresh}
        
        # Добавляем исторические данные, которых нет в свежих
        merged_reserves = formatted_fresh.copy()
        
        for historical in historical_data:
            hist_id = str(historical.get('id', ''))
            if hist_id and hist_id not in fresh_ids:
                merged_reserves.append(historical)
        
        logger.info(f"Объединено {len(merged_reserves)} резервов "
                   f"({len(formatted_fresh)} свежих + {len(merged_reserves) - len(formatted_fresh)} исторических)")
        
        return merged_reserves
    
    async def _update_reserves_sheet(self, reserves: List[Dict]) -> int:
        """Обновление листа 'Reserves RP'"""
        try:
            if not reserves:
                return 0
            
            # Подготавливаем заголовки
            headers = [
                'ID', 'Reserve ID', 'Имя', 'Телефон', 'Email',
                'Дата и время', 'Статус', 'Сумма заказа', 'Количество',
                'Источник', 'Создано', 'Обновлено'
            ]
            
            # Подготавливаем данные для записи
            sheet_data = [headers]
            
            for reserve in reserves:
                row = [
                    str(reserve.get('id', '')),
                    str(reserve.get('reserve_id', '')),
                    str(reserve.get('name', '')),
                    str(reserve.get('phone', '')),
                    str(reserve.get('email', '')),
                    str(reserve.get('time_from', '')),
                    str(reserve.get('status', '')),
                    float(reserve.get('order_sum', 0)),
                    int(reserve.get('count', 0)),
                    str(reserve.get('source', '')),
                    str(reserve.get('created_at', '')),
                    str(reserve.get('updated_at', ''))
                ]
                sheet_data.append(row)
            
            # Очищаем лист и записываем новые данные
            self.sheets_service.clear_sheet("Reserves RP")
            self.sheets_service.write_data("Reserves RP", sheet_data)
            
            logger.info(f"Обновлён лист 'Reserves RP': {len(reserves)} записей")
            return len(reserves)
            
        except Exception as e:
            logger.error(f"Ошибка при обновлении листа резервов: {e}")
            return 0
    
    async def _update_guests_sheet(self, guests: List[Dict]) -> int:
        """Обновление листа 'Guests RP'"""
        try:
            if not guests:
                return 0
            
            # Подготавливаем заголовки
            headers = [
                'Имя', 'Телефон', 'Email', 'Количество визитов',
                'Общая сумма', 'Первый визит', 'Последний визит',
                'Визит 1', 'Визит 2', 'Визит 3', 'Визит 4', 'Визит 5',
                'Визит 6', 'Визит 7', 'Визит 8', 'Визит 9', 'Визит 10'
            ]
            
            # Подготавливаем данные для записи
            sheet_data = [headers]
            
            for guest in guests:
                # Формируем строку с последними 10 суммами визитов
                visit_sums = []
                for i in range(10):
                    if i < len(guest.get('visits', [])):
                        visit_sums.append(guest['visits'][i].get('sum', 0))
                    else:
                        visit_sums.append('')
                
                row = [
                    str(guest.get('name', '')),
                    str(guest.get('phone', '')),
                    str(guest.get('email', '')),
                    int(guest.get('visits_count', 0)),
                    float(guest.get('total_sum', 0)),
                    str(guest.get('first_visit', '')),
                    str(guest.get('last_visit', '')),
                ] + visit_sums
                
                sheet_data.append(row)
            
            # Очищаем лист и записываем новые данные
            self.sheets_service.clear_sheet("Guests RP")
            self.sheets_service.write_data("Guests RP", sheet_data)
            
            logger.info(f"Обновлён лист 'Guests RP': {len(guests)} записей")
            return len(guests)
            
        except Exception as e:
            logger.error(f"Ошибка при обновлении листа гостей: {e}")
            return 0
    
    def get_update_summary(self, stats: Dict[str, int]) -> str:
        """
        Формирование сводки об обновлении
        
        Args:
            stats: Статистика обновления
            
        Returns:
            Текстовая сводка
        """
        if stats.get('error'):
            return f"❌ Ошибка обновления данных RestoPlace:\n{stats['error']}"
        
        summary = "📊 Обновление данных RestoPlace завершено\n\n"
        summary += f"🔄 Резервов обновлено: {stats.get('reserves_updated', 0)}\n"
        summary += f"👥 Гостей обработано: {stats.get('guests_updated', 0)}\n"
        summary += f"📈 Всего резервов: {stats.get('total_reserves', 0)}\n"
        summary += f"🆕 Из API: {stats.get('api_reserves', 0)}\n"
        summary += f"📚 Исторических: {stats.get('historical_reserves', 0)}\n\n"
        summary += f"⏰ Время обновления: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        summary += f"🔗 [Открыть таблицу](https://docs.google.com/spreadsheets/d/{self.sheets_service.spreadsheet_id})"
        
        return summary
