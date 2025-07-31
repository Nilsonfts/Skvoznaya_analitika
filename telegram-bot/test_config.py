#!/usr/bin/env python3
"""
Скрипт для тестирования конфигурации Google Sheets
"""

import sys
import os

# Добавляем текущую директорию в path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import LEAD_SOURCES, SHEETS_CONFIG

def test_configuration():
    """Тестирование конфигурации"""
    print("=== Тестирование конфигурации LEAD_SOURCES ===\n")
    
    # Проверяем наличие всех источников
    required_sources = ['site', 'social', 'guests']
    for source in required_sources:
        if source in LEAD_SOURCES:
            print(f"✅ Источник '{source}' найден")
            config = LEAD_SOURCES[source]
            print(f"   Лист: {config['sheet_name']}")
            print(f"   Колонок: {len(config['columns'])}")
            
            # Показываем первые 5 колонок
            columns = list(config['columns'].items())[:5]
            for key, value in columns:
                print(f"   {key}: '{value}'")
            if len(config['columns']) > 5:
                print(f"   ... и еще {len(config['columns']) - 5} колонок")
            print()
        else:
            print(f"❌ Источник '{source}' НЕ найден")
    
    print("=== Детали конфигурации ===\n")
    
    # Проверяем конфигурацию для сайта
    if 'site' in LEAD_SOURCES:
        site_config = LEAD_SOURCES['site']
        print(f"Сайт ({site_config['sheet_name']}):")
        print(f"  - Телефон: {site_config['columns']['phone']}")
        print(f"  - Email: {site_config['columns']['email']}")
        print(f"  - UTM Source: {site_config['columns']['utm_source']}")
        print()
    
    # Проверяем конфигурацию для соцсетей
    if 'social' in LEAD_SOURCES:
        social_config = LEAD_SOURCES['social']
        print(f"Соцсети ({social_config['sheet_name']}):")
        print(f"  - Телефон: {social_config['columns']['phone']}")
        print(f"  - Имя: {social_config['columns']['name']}")
        print(f"  - UTM Source: {social_config['columns']['utm_source']}")
        print()
    
    # Проверяем конфигурацию для гостей
    if 'guests' in LEAD_SOURCES:
        guests_config = LEAD_SOURCES['guests']
        print(f"Гости ({guests_config['sheet_name']}):")
        print(f"  - Телефон: {guests_config['columns']['phone']}")
        print(f"  - Имя: {guests_config['columns']['name']}")
        print(f"  - Количество визитов: {guests_config['columns']['visits_count']}")
        print(f"  - Общий доход: {guests_config['columns']['total_revenue']}")
        
        # Проверяем визиты
        visit_columns = [k for k in guests_config['columns'].keys() if k.startswith('visit_')]
        print(f"  - Колонок визитов: {len(visit_columns)}")
        for visit_col in visit_columns[:3]:  # Показываем первые 3
            print(f"    {visit_col}: {guests_config['columns'][visit_col]}")
        if len(visit_columns) > 3:
            print(f"    ... и еще {len(visit_columns) - 3} визитов")
        print()
    
    print("=== Старая конфигурация SHEETS_CONFIG ===\n")
    for key, value in SHEETS_CONFIG.items():
        print(f"{key}: {value}")
    
    print("\n✅ Тестирование завершено!")

if __name__ == "__main__":
    test_configuration()
