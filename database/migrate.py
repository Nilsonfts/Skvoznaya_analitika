"""
Скрипт миграции данных из Google Sheets в PostgreSQL
"""

import asyncio
import logging
import sys
from datetime import datetime, date
from typing import Dict, List
from services.database import DatabaseService
from services.google_sheets import GoogleSheetsService
from utils.calculations import determine_client_segment
from config import DATABASE_URL, SPREADSHEET_ID

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataMigrationService:
    """Сервис для миграции данных из Google Sheets в PostgreSQL"""
    
    def __init__(self):
        self.db_service = DatabaseService(DATABASE_URL)
        self.sheets_service = GoogleSheetsService()
    
    async def migrate_all_data(self):
        """Полная миграция всех данных"""
        try:
            logger.info("Начинаем полную миграцию данных")
            
            # Инициализация соединения с БД
            await self.db_service.init_pool()
            
            # Создание схемы БД
            await self.db_service.execute_script('database/schema.sql')
            
            # Миграция каналов
            await self.migrate_channels()
            
            # Миграция лидов из разных листов
            await self.migrate_leads_from_site()
            await self.migrate_leads_from_social()
            
            # Миграция гостей и создание клиентов
            await self.migrate_guests_to_clients()
            
            # Миграция резервов RestoPlace
            await self.migrate_restoplace_reserves()
            
            logger.info("Миграция данных завершена успешно")
            
        except Exception as e:
            logger.error(f"Ошибка миграции данных: {e}")
            raise
        finally:
            await self.db_service.close_pool()
    
    async def migrate_channels(self):
        """Миграция каналов из конфигурации"""
        logger.info("Миграция каналов...")
        
        # Базовые каналы уже создаются в schema.sql
        # Здесь можем добавить дополнительные каналы если нужно
        
        channels = await self.db_service.get_channels()
        logger.info(f"Создано каналов: {len(channels)}")
    
    async def migrate_leads_from_site(self):
        """Миграция лидов с сайта"""
        logger.info("Миграция лидов с сайта...")
        
        try:
            # Читаем данные из листа "Заявки Сайт"
            sheet_data = self.sheets_service.read_sheet("Заявки Сайт")
            
            if not sheet_data or len(sheet_data) < 2:
                logger.warning("Нет данных в листе 'Заявки Сайт'")
                return
            
            headers = [h.lower().replace(' ', '_') for h in sheet_data[0]]
            site_channel = await self.db_service.get_channel_by_name("Сайт")
            
            if not site_channel:
                logger.error("Канал 'Сайт' не найден")
                return
            
            migrated_count = 0
            
            for row in sheet_data[1:]:
                if len(row) < len(headers):
                    continue
                
                # Создаем словарь из строки
                lead_dict = {}
                for i, header in enumerate(headers):
                    lead_dict[header] = row[i] if i < len(row) else ""
                
                # Подготавливаем данные лида
                lead_data = {
                    'name': lead_dict.get('имя', lead_dict.get('name', '')),
                    'phone': self._format_phone(lead_dict.get('телефон', lead_dict.get('phone', ''))),
                    'email': lead_dict.get('email', lead_dict.get('почта', '')),
                    'channel_id': site_channel['id'],
                    'source': 'Сайт',
                    'utm_source': lead_dict.get('utm_source', ''),
                    'utm_medium': lead_dict.get('utm_medium', ''),
                    'utm_campaign': lead_dict.get('utm_campaign', ''),
                    'lead_date': self._parse_date(lead_dict.get('дата', lead_dict.get('date', ''))),
                    'status': 'imported',
                    'notes': f"Импорт из Google Sheets: {lead_dict.get('комментарий', '')}"
                }
                
                if lead_data['phone']:  # Создаем только если есть телефон
                    await self.db_service.create_lead(lead_data)
                    migrated_count += 1
            
            logger.info(f"Мигрировано лидов с сайта: {migrated_count}")
            
        except Exception as e:
            logger.error(f"Ошибка миграции лидов с сайта: {e}")
    
    async def migrate_leads_from_social(self):
        """Миграция лидов из соцсетей"""
        logger.info("Миграция лидов из соцсетей...")
        
        try:
            sheet_data = self.sheets_service.read_sheet("Заявки Соц сети")
            
            if not sheet_data or len(sheet_data) < 2:
                logger.warning("Нет данных в листе 'Заявки Соц сети'")
                return
            
            headers = [h.lower().replace(' ', '_') for h in sheet_data[0]]
            migrated_count = 0
            
            for row in sheet_data[1:]:
                if len(row) < len(headers):
                    continue
                
                lead_dict = {}
                for i, header in enumerate(headers):
                    lead_dict[header] = row[i] if i < len(row) else ""
                
                # Определяем канал по источнику
                source = lead_dict.get('источник', lead_dict.get('source', '')).lower()
                channel_name = self._map_source_to_channel(source)
                channel = await self.db_service.get_channel_by_name(channel_name)
                
                if not channel:
                    logger.warning(f"Канал '{channel_name}' не найден для источника '{source}'")
                    continue
                
                lead_data = {
                    'name': lead_dict.get('имя', lead_dict.get('name', '')),
                    'phone': self._format_phone(lead_dict.get('телефон', lead_dict.get('phone', ''))),
                    'email': lead_dict.get('email', lead_dict.get('почта', '')),
                    'channel_id': channel['id'],
                    'source': source,
                    'lead_date': self._parse_date(lead_dict.get('дата', lead_dict.get('date', ''))),
                    'status': 'imported',
                    'notes': f"Импорт из соцсетей: {lead_dict.get('комментарий', '')}"
                }
                
                if lead_data['phone']:
                    await self.db_service.create_lead(lead_data)
                    migrated_count += 1
            
            logger.info(f"Мигрировано лидов из соцсетей: {migrated_count}")
            
        except Exception as e:
            logger.error(f"Ошибка миграции лидов из соцсетей: {e}")
    
    async def migrate_guests_to_clients(self):
        """Миграция гостей в клиентов с посещениями"""
        logger.info("Миграция гостей в клиентов...")
        
        try:
            sheet_data = self.sheets_service.read_sheet("Guests RP")
            
            if not sheet_data or len(sheet_data) < 2:
                logger.warning("Нет данных в листе 'Guests RP'")
                return
            
            headers = [h.lower().replace(' ', '_') for h in sheet_data[0]]
            migrated_count = 0
            
            # Получаем канал RestoPlace
            rp_channel = await self.db_service.get_channel_by_name("RestoPlace")
            
            for row in sheet_data[1:]:
                if len(row) < len(headers):
                    continue
                
                guest_dict = {}
                for i, header in enumerate(headers):
                    guest_dict[header] = row[i] if i < len(row) else ""
                
                phone = self._format_phone(guest_dict.get('телефон', guest_dict.get('phone', '')))
                if not phone:
                    continue
                
                # Собираем суммы визитов
                visit_amounts = []
                for i in range(1, 11):  # Визит 1 - Визит 10
                    visit_key = f'визит_{i}'
                    if visit_key not in guest_dict:
                        visit_key = f'visit_{i}'
                    
                    amount_str = guest_dict.get(visit_key, '')
                    if amount_str and str(amount_str).replace('.', '').replace(',', '').isdigit():
                        amount = float(str(amount_str).replace(',', '.'))
                        if amount > 0:
                            visit_amounts.append(amount)
                
                total_visits = int(guest_dict.get('количество_визитов', guest_dict.get('visits_count', 0)) or 0)
                total_revenue = float(guest_dict.get('общая_сумма', guest_dict.get('total_sum', 0)) or 0)
                
                # Определяем сегмент клиента
                segment = determine_client_segment(total_visits, total_revenue, visit_amounts)
                
                # Создаем клиента
                client_data = {
                    'name': guest_dict.get('имя', guest_dict.get('name', '')),
                    'phone': phone,
                    'email': guest_dict.get('email', guest_dict.get('почта', '')),
                    'first_visit_date': self._parse_date(guest_dict.get('первый_визит', guest_dict.get('first_visit', ''))),
                    'last_visit_date': self._parse_date(guest_dict.get('последний_визит', guest_dict.get('last_visit', ''))),
                    'total_visits': total_visits,
                    'total_revenue': total_revenue,
                    'average_check': total_revenue / total_visits if total_visits > 0 else 0,
                    'segment': segment,
                    'channel_id': rp_channel['id'] if rp_channel else None
                }
                
                client_id = await self.db_service.create_or_update_client(client_data)
                
                # Создаем записи о посещениях
                for i, amount in enumerate(visit_amounts):
                    # Примерные даты посещений (распределяем по последним месяцам)
                    visit_date = datetime.now().replace(day=1) - timedelta(days=i*30)
                    
                    visit_data = {
                        'client_id': client_id,
                        'visit_date': visit_date,
                        'amount': amount,
                        'guests_count': 1,
                        'notes': f"Импорт из Guests RP (визит #{i+1})"
                    }
                    
                    await self.db_service.create_visit(visit_data)
                
                migrated_count += 1
            
            logger.info(f"Мигрировано клиентов: {migrated_count}")
            
        except Exception as e:
            logger.error(f"Ошибка миграции гостей: {e}")
    
    async def migrate_restoplace_reserves(self):
        """Миграция резервов RestoPlace"""
        logger.info("Миграция резервов RestoPlace...")
        
        try:
            sheet_data = self.sheets_service.read_sheet("Reserves RP")
            
            if not sheet_data or len(sheet_data) < 2:
                logger.warning("Нет данных в листе 'Reserves RP'")
                return
            
            headers = [h.lower().replace(' ', '_') for h in sheet_data[0]]
            migrated_count = 0
            
            for row in sheet_data[1:]:
                if len(row) < len(headers):
                    continue
                
                reserve_dict = {}
                for i, header in enumerate(headers):
                    reserve_dict[header] = row[i] if i < len(row) else ""
                
                # Вставляем резерв напрямую в таблицу reserves
                query = """
                    INSERT INTO reserves (reserve_id, guest_name, phone, email, 
                                        visit_datetime, status, amount, guests_count, source)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    ON CONFLICT (reserve_id) DO NOTHING
                """
                
                async with self.db_service.pool.acquire() as conn:
                    await conn.execute(
                        query,
                        reserve_dict.get('reserve_id', reserve_dict.get('id', '')),
                        reserve_dict.get('имя', reserve_dict.get('name', '')),
                        self._format_phone(reserve_dict.get('телефон', reserve_dict.get('phone', ''))),
                        reserve_dict.get('email', ''),
                        self._parse_datetime(reserve_dict.get('дата_и_время', reserve_dict.get('datetime', ''))),
                        reserve_dict.get('статус', reserve_dict.get('status', '')),
                        float(reserve_dict.get('сумма_заказа', reserve_dict.get('amount', 0)) or 0),
                        int(reserve_dict.get('количество', reserve_dict.get('count', 1)) or 1),
                        reserve_dict.get('источник', reserve_dict.get('source', 'RestoPlace'))
                    )
                
                migrated_count += 1
            
            logger.info(f"Мигрировано резервов: {migrated_count}")
            
        except Exception as e:
            logger.error(f"Ошибка миграции резервов: {e}")
    
    def _format_phone(self, phone: str) -> str:
        """Форматирование телефона"""
        if not phone:
            return ''
        
        digits = ''.join(filter(str.isdigit, str(phone)))
        
        if digits.startswith('8') and len(digits) == 11:
            digits = '7' + digits[1:]
        
        if digits.startswith('7') and len(digits) == 11:
            return '+' + digits
        
        return phone if phone else ''
    
    def _parse_date(self, date_str: str) -> date:
        """Парсинг даты"""
        if not date_str:
            return datetime.now().date()
        
        try:
            # Пробуем разные форматы
            formats = ['%d.%m.%Y', '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y']
            for fmt in formats:
                try:
                    return datetime.strptime(str(date_str), fmt).date()
                except ValueError:
                    continue
            
            return datetime.now().date()
        except:
            return datetime.now().date()
    
    def _parse_datetime(self, datetime_str: str) -> datetime:
        """Парсинг даты и времени"""
        if not datetime_str:
            return datetime.now()
        
        try:
            formats = [
                '%d.%m.%Y %H:%M:%S',
                '%Y-%m-%d %H:%M:%S',
                '%d.%m.%Y %H:%M',
                '%Y-%m-%d %H:%M',
                '%d.%m.%Y',
                '%Y-%m-%d'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(str(datetime_str), fmt)
                except ValueError:
                    continue
            
            return datetime.now()
        except:
            return datetime.now()
    
    def _map_source_to_channel(self, source: str) -> str:
        """Маппинг источника на канал"""
        source_lower = source.lower()
        
        if 'yandex' in source_lower or 'яндекс' in source_lower:
            return 'Yandex'
        elif 'google' in source_lower or 'гугл' in source_lower:
            return 'Google'
        elif 'vk' in source_lower or 'вконтакте' in source_lower:
            return 'VK'
        elif 'instagram' in source_lower or 'инстаграм' in source_lower:
            return 'Instagram'
        elif 'site' in source_lower or 'сайт' in source_lower:
            return 'Сайт'
        elif 'recommend' in source_lower or 'рекоменд' in source_lower:
            return 'Рекомендации'
        else:
            return 'Сайт'  # По умолчанию

async def main():
    """Основная функция миграции"""
    if len(sys.argv) > 1 and sys.argv[1] == '--migrate':
        migration_service = DataMigrationService()
        await migration_service.migrate_all_data()
        print("✅ Миграция данных завершена!")
    else:
        print("Для запуска миграции используйте: python database/migrate.py --migrate")

if __name__ == "__main__":
    asyncio.run(main())
