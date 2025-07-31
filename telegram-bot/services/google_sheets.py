"""
Сервис для работы с Google Sheets
"""

import logging
import gspread
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd

from config import SPREADSHEET_ID, GOOGLE_CREDENTIALS_FILE, SHEETS_CONFIG, COLORS

logger = logging.getLogger(__name__)

class GoogleSheetsService:
    def __init__(self):
        """Инициализация сервиса Google Sheets"""
        try:
            self.gc = gspread.service_account(filename=GOOGLE_CREDENTIALS_FILE)
            self.spreadsheet = self.gc.open_by_key(SPREADSHEET_ID)
            logger.info("Google Sheets сервис инициализирован")
        except Exception as e:
            logger.error(f"Ошибка инициализации Google Sheets: {e}")
            raise
    
    def get_worksheet(self, sheet_name: str, create_if_not_exists: bool = False):
        """Получить рабочий лист по имени"""
        try:
            return self.spreadsheet.worksheet(sheet_name)
        except gspread.WorksheetNotFound:
            if create_if_not_exists:
                logger.info(f"Создаю новый лист: {sheet_name}")
                return self.spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=50)
            else:
                logger.error(f"Лист {sheet_name} не найден")
                return None
    
    def read_sheet_data(self, sheet_name: str) -> List[Dict[str, Any]]:
        """Чтение данных из листа"""
        try:
            worksheet = self.spreadsheet.worksheet(sheet_name)
            
            # Получаем все значения включая заголовки
            all_values = worksheet.get_all_values()
            
            if not all_values:
                logger.warning(f"Лист {sheet_name} пуст")
                return []
            
            # Первая строка содержит заголовки
            headers = all_values[0]
            
            # Преобразуем данные в список словарей
            data = []
            for row in all_values[1:]:
                # Создаем словарь, где ключи - это заголовки столбцов
                row_dict = {}
                for i, value in enumerate(row):
                    if i < len(headers):
                        # Очищаем значения от лишних пробелов
                        clean_value = str(value).strip() if value else ''
                        row_dict[headers[i]] = clean_value
                
                # Добавляем строку только если есть хотя бы одно непустое значение
                if any(row_dict.values()):
                    data.append(row_dict)
            
            logger.info(f"Загружено {len(data)} записей из листа {sheet_name}")
            return data
            
        except Exception as e:
            logger.error(f"Ошибка при чтении листа {sheet_name}: {e}")
            return []
    
    def write_sheet_data(self, sheet_name: str, data: List[Dict[str, Any]], 
                        clear_existing: bool = True) -> bool:
        """Запись данных в лист"""
        try:
            worksheet = self.get_worksheet(sheet_name, create_if_not_exists=True)
            if not worksheet:
                return False
            
            if not data:
                logger.warning(f"Нет данных для записи в {sheet_name}")
                return True
            
            # Очистка существующих данных
            if clear_existing:
                worksheet.clear()
            
            # Создание DataFrame для удобной работы
            df = pd.DataFrame(data)
            
            # Запись заголовков
            headers = df.columns.tolist()
            worksheet.update('A1', [headers])
            
            # Запись данных
            if len(df) > 0:
                values = df.values.tolist()
                worksheet.update(f'A2:Z{len(values)+1}', values)
            
            logger.info(f"Записано {len(data)} записей в лист {sheet_name}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка записи данных в {sheet_name}: {e}")
            return False
    
    def append_sheet_data(self, sheet_name: str, data: List[Dict[str, Any]]) -> bool:
        """Добавление данных в конец листа"""
        try:
            worksheet = self.get_worksheet(sheet_name, create_if_not_exists=True)
            if not worksheet:
                return False
            
            if not data:
                return True
            
            # Если лист пустой, добавляем заголовки
            existing_data = worksheet.get_all_records()
            if not existing_data:
                headers = list(data[0].keys())
                worksheet.update('A1', [headers])
            
            # Добавление новых данных
            df = pd.DataFrame(data)
            values = df.values.tolist()
            worksheet.append_rows(values)
            
            logger.info(f"Добавлено {len(data)} записей в лист {sheet_name}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка добавления данных в {sheet_name}: {e}")
            return False
    
    def get_leads_from_site(self) -> List[Dict[str, Any]]:
        """Получение лидов с сайта"""
        from config import LEAD_SOURCES
        
        source_config = LEAD_SOURCES['site']
        leads = self.read_sheet_data(source_config['sheet_name'])
        
        # Стандартизация названий колонок согласно конфигурации
        standardized_leads = []
        for lead in leads:
            standardized_lead = {
                'date': lead.get(source_config['columns']['date'], ''),
                'name': lead.get(source_config['columns']['name'], ''),
                'phone': lead.get(source_config['columns']['phone'], ''),
                'email': lead.get(source_config['columns']['email'], ''),
                'utm_source': lead.get(source_config['columns']['utm_source'], ''),
                'utm_medium': lead.get(source_config['columns']['utm_medium'], ''),
                'utm_campaign': lead.get(source_config['columns']['utm_campaign'], ''),
                'utm_content': lead.get(source_config['columns']['utm_content'], ''),
                'utm_term': lead.get(source_config['columns']['utm_term'], ''),
                'ga_client_id': lead.get(source_config['columns']['ga_client_id'], ''),
                'ym_client_id': lead.get(source_config['columns']['ym_client_id'], ''),
                'form_name': lead.get(source_config['columns']['form_name'], ''),
                'button_text': lead.get(source_config['columns']['button_text'], ''),
                'source': 'site'
            }
            standardized_leads.append(standardized_lead)
        
        return standardized_leads
    
    def get_leads_from_social(self) -> List[Dict[str, Any]]:
        """Получение лидов из социальных сетей"""
        from config import LEAD_SOURCES
        
        source_config = LEAD_SOURCES['social']
        leads = self.read_sheet_data(source_config['sheet_name'])
        
        # Стандартизация названий колонок согласно конфигурации
        standardized_leads = []
        for lead in leads:
            standardized_lead = {
                'date': lead.get(source_config['columns']['date'], ''),
                'name': lead.get(source_config['columns']['name'], ''),
                'phone': lead.get(source_config['columns']['phone'], ''),
                'email': lead.get(source_config['columns']['email'], ''),  # Может быть пустым
                'utm_source': lead.get(source_config['columns']['utm_source'], ''),
                'utm_medium': lead.get(source_config['columns']['utm_medium'], ''),
                'utm_campaign': lead.get(source_config['columns']['utm_campaign'], ''),
                'utm_content': lead.get(source_config['columns']['utm_content'], ''),
                'utm_term': lead.get(source_config['columns']['utm_term'], ''),
                'ga_client_id': lead.get(source_config['columns']['ga_client_id'], ''),  # Может быть пустым
                'ym_client_id': lead.get(source_config['columns']['ym_client_id'], ''),   # Может быть пустым
                'form_name': 'Социальные сети',
                'button_text': '',
                'source': 'social'
            }
            standardized_leads.append(standardized_lead)
        
        return standardized_leads
    
    def get_guests_data(self) -> List[Dict[str, Any]]:
        """Получение данных о клиентах из листа Guests RP"""
        from config import LEAD_SOURCES
        
        source_config = LEAD_SOURCES['guests']
        guests_raw = self.read_sheet_data(source_config['sheet_name'])
        
        # Стандартизация данных клиентов
        standardized_guests = []
        for guest in guests_raw:
            # Сбор сумм по визитам
            visit_amounts = []
            for i in range(1, 11):  # До 10 визитов
                visit_key = f'visit_{i}'
                if visit_key in source_config['columns']:
                    amount = guest.get(source_config['columns'][visit_key], 0)
                    if amount:
                        try:
                            visit_amounts.append(float(amount))
                        except (ValueError, TypeError):
                            pass
            
            standardized_guest = {
                'name': guest.get(source_config['columns']['name'], ''),
                'phone': guest.get(source_config['columns']['phone'], ''),
                'email': guest.get(source_config['columns']['email'], ''),
                'visits_count': int(guest.get(source_config['columns']['visits_count'], 0) or 0),
                'total_revenue': float(guest.get(source_config['columns']['total_revenue'], 0) or 0),
                'first_visit_date': guest.get(source_config['columns']['first_visit'], ''),
                'last_visit_date': guest.get(source_config['columns']['last_visit'], ''),
                'visit_amounts': visit_amounts  # Суммы по каждому визиту
            }
            standardized_guests.append(standardized_guest)
        
        return standardized_guests
    
    def create_dashboard(self, sheet_name: str, dashboard_data: Dict[str, Any]) -> bool:
        """Создание дашборда с данными и форматированием"""
        try:
            worksheet = self.get_worksheet(sheet_name, create_if_not_exists=True)
            if not worksheet:
                return False
            
            # Очистка листа
            worksheet.clear()
            
            # Установка базовых свойств
            worksheet.update('A1', dashboard_data.get('title', ''))
            
            # Применение форматирования
            self._apply_dashboard_formatting(worksheet, dashboard_data)
            
            # Запись данных
            if 'tables' in dashboard_data:
                current_row = 3  # Начинаем с 3 строки после заголовка
                
                for table in dashboard_data['tables']:
                    # Заголовок таблицы
                    if 'table_title' in table:
                        worksheet.update(f'A{current_row}', table['table_title'])
                        current_row += 2
                    
                    # Заголовки столбцов
                    if 'headers' in table:
                        worksheet.update(f'A{current_row}', [table['headers']])
                        current_row += 1
                    
                    # Данные таблицы
                    if 'data' in table and table['data']:
                        range_end = chr(ord('A') + len(table['data'][0]) - 1)
                        worksheet.update(f'A{current_row}:{range_end}{current_row + len(table["data"]) - 1}', 
                                       table['data'])
                        current_row += len(table['data']) + 2
            
            # Применение условного форматирования
            self._apply_conditional_formatting(worksheet, dashboard_data)
            
            # Автоширина столбцов
            self._auto_resize_columns(worksheet)
            
            logger.info(f"Дашборд {sheet_name} создан успешно")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка создания дашборда {sheet_name}: {e}")
            return False
    
    def _apply_dashboard_formatting(self, worksheet, dashboard_data: Dict[str, Any]):
        """Применение базового форматирования к дашборду"""
        try:
            # Форматирование заголовка
            worksheet.format('A1:Z1', {
                'backgroundColor': {'red': 0.2, 'green': 0.4, 'blue': 0.8},
                'textFormat': {
                    'foregroundColor': {'red': 1.0, 'green': 1.0, 'blue': 1.0},
                    'fontSize': 16,
                    'bold': True
                },
                'horizontalAlignment': 'CENTER'
            })
            
            # Замораживание первой строки
            worksheet.freeze(rows=1)
            
        except Exception as e:
            logger.error(f"Ошибка применения форматирования: {e}")
    
    def _apply_conditional_formatting(self, worksheet, dashboard_data: Dict[str, Any]):
        """Применение условного форматирования"""
        try:
            # Пример условного форматирования для ROI
            if 'roi_column' in dashboard_data:
                col = dashboard_data['roi_column']
                
                # Зеленый для положительного ROI
                worksheet.add_conditional_format(f'{col}2:{col}1000', {
                    'type': 'NUMBER_GREATER',
                    'values': [{'userEnteredValue': '0'}],
                    'format': {
                        'backgroundColor': {'red': 0.8, 'green': 1.0, 'blue': 0.8}
                    }
                })
                
                # Красный для отрицательного ROI
                worksheet.add_conditional_format(f'{col}2:{col}1000', {
                    'type': 'NUMBER_LESS',
                    'values': [{'userEnteredValue': '0'}],
                    'format': {
                        'backgroundColor': {'red': 1.0, 'green': 0.8, 'blue': 0.8}
                    }
                })
                
        except Exception as e:
            logger.error(f"Ошибка применения условного форматирования: {e}")
    
    def _auto_resize_columns(self, worksheet):
        """Автоматическое изменение ширины столбцов"""
        try:
            # Получаем данные для определения ширины
            data = worksheet.get_all_values()
            if not data:
                return
            
            # Вычисляем максимальную ширину для каждого столбца
            max_widths = []
            for col_idx in range(len(data[0])):
                max_width = 0
                for row in data:
                    if col_idx < len(row):
                        cell_length = len(str(row[col_idx]))
                        max_width = max(max_width, cell_length)
                max_widths.append(min(max_width * 8, 300))  # Ограничиваем максимальную ширину
            
            # Применяем ширину столбцов
            for i, width in enumerate(max_widths):
                worksheet.columns_auto_resize(i, i)
                
        except Exception as e:
            logger.error(f"Ошибка автоизменения ширины столбцов: {e}")
    
    def backup_spreadsheet(self, backup_name: str = None) -> bool:
        """Создание резервной копии таблицы"""
        try:
            if not backup_name:
                backup_name = f"Backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Копирование таблицы
            backup = self.gc.copy(SPREADSHEET_ID, title=backup_name)
            logger.info(f"Создана резервная копия: {backup_name}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка создания резервной копии: {e}")
            return False
