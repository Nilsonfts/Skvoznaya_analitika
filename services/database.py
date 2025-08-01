"""
Сервис для работы с базой данных PostgreSQL
"""

import asyncio
import logging
import asyncpg
from typing import List, Dict, Optional, Any
from datetime import datetime, date
from config import DATABASE_URL, USE_POSTGRES

logger = logging.getLogger(__name__)

class DatabaseService:
    """Сервис для работы с PostgreSQL"""
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or DATABASE_URL
        self.pool = None
        
    async def init_pool(self):
        """Инициализация пула соединений"""
        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=1,
                max_size=10,
                command_timeout=60
            )
            logger.info("Пул соединений с базой данных создан")
        except Exception as e:
            logger.error(f"Ошибка создания пула соединений: {e}")
            raise
    
    async def close_pool(self):
        """Закрытие пула соединений"""
        if self.pool:
            await self.pool.close()
            logger.info("Пул соединений с базой данных закрыт")
    
    async def execute_script(self, script_path: str):
        """Выполнение SQL скрипта"""
        try:
            with open(script_path, 'r', encoding='utf-8') as file:
                script = file.read()
            
            async with self.pool.acquire() as conn:
                await conn.execute(script)
                logger.info(f"Скрипт {script_path} выполнен успешно")
        except Exception as e:
            logger.error(f"Ошибка выполнения скрипта {script_path}: {e}")
            raise
    
    # CRUD операции для каналов
    async def get_channels(self, active_only: bool = True) -> List[Dict]:
        """Получение списка каналов"""
        query = "SELECT * FROM channels"
        if active_only:
            query += " WHERE is_active = TRUE"
        query += " ORDER BY name"
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query)
            return [dict(row) for row in rows]
    
    async def get_channel_by_name(self, name: str) -> Optional[Dict]:
        """Получение канала по имени"""
        query = "SELECT * FROM channels WHERE name = $1"
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, name)
            return dict(row) if row else None
    
    async def create_channel(self, name: str, cost_per_month: float = 0, 
                           description: str = "") -> int:
        """Создание нового канала"""
        query = """
            INSERT INTO channels (name, cost_per_month, description)
            VALUES ($1, $2, $3)
            RETURNING id
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, name, cost_per_month, description)
            return row['id']
    
    # CRUD операции для лидов
    async def create_lead(self, lead_data: Dict) -> int:
        """Создание нового лида"""
        query = """
            INSERT INTO leads (name, phone, email, channel_id, source, 
                             utm_source, utm_medium, utm_campaign, lead_date, status, notes)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            RETURNING id
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                lead_data.get('name'),
                lead_data.get('phone'),
                lead_data.get('email'),
                lead_data.get('channel_id'),
                lead_data.get('source'),
                lead_data.get('utm_source'),
                lead_data.get('utm_medium'),
                lead_data.get('utm_campaign'),
                lead_data.get('lead_date', datetime.now()),
                lead_data.get('status', 'new'),
                lead_data.get('notes')
            )
            return row['id']
    
    async def get_leads(self, channel_id: Optional[int] = None, 
                       start_date: Optional[date] = None,
                       end_date: Optional[date] = None) -> List[Dict]:
        """Получение лидов с фильтрацией"""
        conditions = []
        params = []
        param_count = 0
        
        if channel_id:
            param_count += 1
            conditions.append(f"channel_id = ${param_count}")
            params.append(channel_id)
        
        if start_date:
            param_count += 1
            conditions.append(f"lead_date >= ${param_count}")
            params.append(start_date)
        
        if end_date:
            param_count += 1
            conditions.append(f"lead_date <= ${param_count}")
            params.append(end_date)
        
        query = "SELECT * FROM leads"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY lead_date DESC"
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]
    
    # CRUD операции для клиентов
    async def create_or_update_client(self, client_data: Dict) -> int:
        """Создание или обновление клиента"""
        # Сначала пытаемся найти существующего клиента по телефону
        existing = await self.get_client_by_phone(client_data.get('phone'))
        
        if existing:
            # Обновляем существующего клиента
            query = """
                UPDATE clients 
                SET name = $1, email = $2, last_visit_date = $3, 
                    total_visits = $4, total_revenue = $5, 
                    average_check = $6, segment = $7, updated_at = CURRENT_TIMESTAMP
                WHERE id = $8
                RETURNING id
            """
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(
                    query,
                    client_data.get('name') or existing['name'],
                    client_data.get('email') or existing['email'],
                    client_data.get('last_visit_date', existing['last_visit_date']),
                    client_data.get('total_visits', existing['total_visits']),
                    client_data.get('total_revenue', existing['total_revenue']),
                    client_data.get('average_check', existing['average_check']),
                    client_data.get('segment', existing['segment']),
                    existing['id']
                )
                return row['id']
        else:
            # Создаем нового клиента
            query = """
                INSERT INTO clients (name, phone, email, first_visit_date, 
                                   last_visit_date, total_visits, total_revenue, 
                                   average_check, segment, lead_id, channel_id)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                RETURNING id
            """
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(
                    query,
                    client_data.get('name'),
                    client_data.get('phone'),
                    client_data.get('email'),
                    client_data.get('first_visit_date'),
                    client_data.get('last_visit_date'),
                    client_data.get('total_visits', 0),
                    client_data.get('total_revenue', 0),
                    client_data.get('average_check', 0),
                    client_data.get('segment', 'Новый'),
                    client_data.get('lead_id'),
                    client_data.get('channel_id')
                )
                return row['id']
    
    async def get_client_by_phone(self, phone: str) -> Optional[Dict]:
        """Получение клиента по телефону"""
        query = "SELECT * FROM clients WHERE phone = $1"
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, phone)
            return dict(row) if row else None
    
    async def get_clients(self, segment: Optional[str] = None) -> List[Dict]:
        """Получение клиентов с фильтрацией"""
        query = "SELECT * FROM clients"
        params = []
        
        if segment:
            query += " WHERE segment = $1"
            params.append(segment)
        
        query += " ORDER BY last_visit_date DESC"
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]
    
    # CRUD операции для посещений
    async def create_visit(self, visit_data: Dict) -> int:
        """Создание записи о посещении"""
        query = """
            INSERT INTO visits (client_id, visit_date, amount, guests_count, 
                              duration_minutes, room_type, services, notes)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                visit_data.get('client_id'),
                visit_data.get('visit_date'),
                visit_data.get('amount'),
                visit_data.get('guests_count', 1),
                visit_data.get('duration_minutes'),
                visit_data.get('room_type'),
                visit_data.get('services'),
                visit_data.get('notes')
            )
            return row['id']
    
    async def get_visits(self, client_id: Optional[int] = None,
                        start_date: Optional[date] = None,
                        end_date: Optional[date] = None) -> List[Dict]:
        """Получение посещений с фильтрацией"""
        conditions = []
        params = []
        param_count = 0
        
        if client_id:
            param_count += 1
            conditions.append(f"client_id = ${param_count}")
            params.append(client_id)
        
        if start_date:
            param_count += 1
            conditions.append(f"visit_date >= ${param_count}")
            params.append(start_date)
        
        if end_date:
            param_count += 1
            conditions.append(f"visit_date <= ${param_count}")
            params.append(end_date)
        
        query = "SELECT * FROM visits"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY visit_date DESC"
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]
    
    # Аналитические запросы
    async def get_channel_analytics(self, start_date: date, end_date: date) -> List[Dict]:
        """Получение аналитики по каналам"""
        query = """
            SELECT 
                c.name,
                c.cost_per_month,
                COUNT(DISTINCT l.id) as leads_count,
                COUNT(DISTINCT cl.id) as clients_count,
                COALESCE(SUM(v.amount), 0) as revenue,
                CASE 
                    WHEN COUNT(DISTINCT cl.id) > 0 
                    THEN c.cost_per_month / COUNT(DISTINCT cl.id)
                    ELSE 0 
                END as cac,
                CASE 
                    WHEN COUNT(DISTINCT cl.id) > 0 
                    THEN COALESCE(SUM(v.amount), 0) / COUNT(DISTINCT cl.id)
                    ELSE 0 
                END as ltv,
                CASE 
                    WHEN c.cost_per_month > 0 
                    THEN (COALESCE(SUM(v.amount), 0) - c.cost_per_month) / c.cost_per_month
                    ELSE 0 
                END as roi,
                CASE 
                    WHEN COUNT(DISTINCT l.id) > 0 
                    THEN COUNT(DISTINCT cl.id)::FLOAT / COUNT(DISTINCT l.id)
                    ELSE 0 
                END as conversion_rate
            FROM channels c
            LEFT JOIN leads l ON c.id = l.channel_id 
                AND l.lead_date BETWEEN $1 AND $2
            LEFT JOIN clients cl ON l.id = cl.lead_id
            LEFT JOIN visits v ON cl.id = v.client_id 
                AND v.visit_date BETWEEN $1 AND $2
            WHERE c.is_active = TRUE
            GROUP BY c.id, c.name, c.cost_per_month
            ORDER BY revenue DESC
        """
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, start_date, end_date)
            return [dict(row) for row in rows]
    
    async def get_segments_analytics(self) -> List[Dict]:
        """Получение аналитики по сегментам клиентов"""
        query = """
            SELECT 
                segment,
                COUNT(*) as clients_count,
                SUM(total_revenue) as total_revenue,
                AVG(total_revenue) as avg_revenue,
                AVG(total_visits) as avg_visits,
                AVG(average_check) as avg_check
            FROM clients
            GROUP BY segment
            ORDER BY clients_count DESC
        """
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query)
            return [dict(row) for row in rows]
    
    # Миграция данных
    async def migrate_data_from_sheets(self, sheets_data: Dict):
        """Миграция данных из Google Sheets"""
        try:
            logger.info("Начинаем миграцию данных из Google Sheets")
            
            # Миграция каналов
            if 'channels' in sheets_data:
                for channel_data in sheets_data['channels']:
                    existing = await self.get_channel_by_name(channel_data['name'])
                    if not existing:
                        await self.create_channel(
                            channel_data['name'],
                            channel_data.get('cost', 0),
                            channel_data.get('description', '')
                        )
            
            # Миграция лидов
            if 'leads' in sheets_data:
                for lead_data in sheets_data['leads']:
                    await self.create_lead(lead_data)
            
            # Миграция клиентов и посещений
            if 'clients' in sheets_data:
                for client_data in sheets_data['clients']:
                    client_id = await self.create_or_update_client(client_data)
                    
                    # Добавляем посещения для клиента
                    if 'visits' in client_data:
                        for visit_data in client_data['visits']:
                            visit_data['client_id'] = client_id
                            await self.create_visit(visit_data)
            
            logger.info("Миграция данных завершена успешно")
            
        except Exception as e:
            logger.error(f"Ошибка миграции данных: {e}")
            raise

# Глобальный экземпляр сервиса
db_service = None

async def get_db_service() -> DatabaseService:
    """Получение экземпляра сервиса базы данных"""
    global db_service
    
    if not USE_POSTGRES:
        return None
    
    if db_service is None:
        db_service = DatabaseService()
        await db_service.init_pool()
    
    return db_service
