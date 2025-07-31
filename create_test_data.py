#!/usr/bin/env python3
"""
Скрипт для создания тестовых данных в Google Sheets
ВНИМАНИЕ: Этот скрипт создает тестовые данные в вашей Google таблице!
Используйте только на тестовой копии.
"""

import sys
import os
from datetime import datetime, timedelta
import random

# Добавляем текущую директорию в path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.google_sheets import GoogleSheetsService
from config import LEAD_SOURCES

def create_test_data():
    """Создание тестовых данных"""
    print("🚨 ВНИМАНИЕ: Этот скрипт создаст тестовые данные в вашей Google таблице!")
    confirmation = input("Продолжить? (yes/no): ")
    
    if confirmation.lower() != 'yes':
        print("Операция отменена.")
        return
    
    try:
        # Инициализация сервиса Google Sheets
        sheets_service = GoogleSheetsService()
        
        # Тестовые данные для сайта
        print("\n📝 Создание тестовых лидов с сайта...")
        site_test_data = [
            {
                'Date': '2024-01-15',
                'Name': 'Анна Смирнова',
                'Очищенный телефон': '+79161234567',
                'Email': 'anna@example.com',
                'utm_source': 'google',
                'utm_medium': 'cpc',
                'utm_campaign': 'promo_winter',
                'utm_content': 'ad_text_1',
                'utm_term': 'салон красоты',
                'ga_client_id': 'GA1.1.123456789.1234567890',
                'ym_client_id': 'YM.1234567890123456789',
                'Form name': 'Форма записи',
                'button_text': 'Записаться'
            },
            {
                'Date': '2024-01-16',
                'Name': 'Елена Петрова',
                'Очищенный телефон': '+79167654321',
                'Email': 'elena@example.com',
                'utm_source': 'yandex',
                'utm_medium': 'cpc',
                'utm_campaign': 'beauty_services',
                'utm_content': 'ad_text_2',
                'utm_term': 'маникюр',
                'ga_client_id': 'GA1.1.987654321.9876543210',
                'ym_client_id': 'YM.9876543210987654321',
                'Form name': 'Быстрая запись',
                'button_text': 'Заказать'
            }
        ]
        
        # Добавляем данные на лист сайта
        site_sheet = sheets_service.spreadsheet.worksheet(LEAD_SOURCES['site']['sheet_name'])
        site_sheet.clear()  # Очищаем лист
        
        # Добавляем заголовки
        headers = list(LEAD_SOURCES['site']['columns'].values())
        site_sheet.append_row(headers)
        
        # Добавляем тестовые данные
        for data in site_test_data:
            row = [data.get(header, '') for header in headers]
            site_sheet.append_row(row)
        
        print(f"✅ Добавлено {len(site_test_data)} лидов с сайта")
        
        # Тестовые данные для соцсетей
        print("\n📱 Создание тестовых лидов из соцсетей...")
        social_test_data = [
            {
                'Дата Заявки': '2024-01-17',
                'Имя Гостя': 'Мария Кузнецова',
                'Телефон': '+79169876543',
                'Email': 'maria@example.com',
                'UTM Source (Источник)': 'instagram',
                'UTM Medium (Канал)': 'social',
                'UTM Campaign (Кампания)': 'stories_promo',
                'UTM Content (Содержание)': 'story_1',
                'UTM Term (Ключ/Дата)': 'инстаграм',
                'ga_id': '',
                'ym_id': ''
            },
            {
                'Дата Заявки': '2024-01-18',
                'Имя Гостя': 'Ольга Волкова',
                'Телефон': '+79163456789',
                'Email': '',
                'UTM Source (Источник)': 'vk',
                'UTM Medium (Канал)': 'social',
                'UTM Campaign (Кампания)': 'vk_group',
                'UTM Content (Содержание)': 'post_1',
                'UTM Term (Ключ/Дата)': 'вконтакте',
                'ga_id': '',
                'ym_id': ''
            }
        ]
        
        # Добавляем данные на лист соцсетей
        social_sheet = sheets_service.spreadsheet.worksheet(LEAD_SOURCES['social']['sheet_name'])
        social_sheet.clear()  # Очищаем лист
        
        # Добавляем заголовки
        headers = list(LEAD_SOURCES['social']['columns'].values())
        social_sheet.append_row(headers)
        
        # Добавляем тестовые данные
        for data in social_test_data:
            row = [data.get(header, '') for header in headers]
            social_sheet.append_row(row)
        
        print(f"✅ Добавлено {len(social_test_data)} лидов из соцсетей")
        
        # Тестовые данные для клиентов
        print("\n👥 Создание тестовых данных клиентов...")
        guests_test_data = [
            {
                'Имя': 'Анна Смирнова',
                'Телефон': '+79161234567',
                'Email': 'anna@example.com',
                'Кол-во визитов': 3,
                'Общая сумма': 8500,
                'Первый визит': '2024-01-20',
                'Последний визит': '2024-01-25',
                'Счёт 1-го визита': 3000,
                'Счёт 2-го визита': 2500,
                'Счёт 3-го визита': 3000,
                'Счёт 4-го визита': '',
                'Счёт 5-го визита': '',
                'Счёт 6-го визита': '',
                'Счёт 7-го визита': '',
                'Счёт 8-го визита': '',
                'Счёт 9-го визита': '',
                'Счёт 10-го визита': ''
            },
            {
                'Имя': 'Мария Кузнецова',
                'Телефон': '+79169876543',
                'Email': 'maria@example.com',
                'Кол-во визитов': 1,
                'Общая сумма': 2000,
                'Первый визит': '2024-01-22',
                'Последний визит': '2024-01-22',
                'Счёт 1-го визита': 2000,
                'Счёт 2-го визита': '',
                'Счёт 3-го визита': '',
                'Счёт 4-го визита': '',
                'Счёт 5-го визита': '',
                'Счёт 6-го визита': '',
                'Счёт 7-го визита': '',
                'Счёт 8-го визита': '',
                'Счёт 9-го визита': '',
                'Счёт 10-го визита': ''
            }
        ]
        
        # Добавляем данные на лист клиентов
        guests_sheet = sheets_service.spreadsheet.worksheet(LEAD_SOURCES['guests']['sheet_name'])
        guests_sheet.clear()  # Очищаем лист
        
        # Добавляем заголовки
        headers = list(LEAD_SOURCES['guests']['columns'].values())
        guests_sheet.append_row(headers)
        
        # Добавляем тестовые данные
        for data in guests_test_data:
            row = [data.get(header, '') for header in headers]
            guests_sheet.append_row(row)
        
        print(f"✅ Добавлено {len(guests_test_data)} клиентов")
        
        print("\n🎉 Тестовые данные успешно созданы!")
        print("\nТеперь вы можете:")
        print("1. Запустить бота: python bot.py")
        print("2. Выполнить команду /merge_leads для объединения данных")
        print("3. Использовать команду /dashboard для создания дашборда")
        
    except Exception as e:
        print(f"❌ Ошибка при создании тестовых данных: {e}")
        print("\nПроверьте:")
        print("1. Настройку Google Sheets API")
        print("2. Права доступа к таблице")
        print("3. Наличие листов с правильными названиями")

if __name__ == "__main__":
    create_test_data()
