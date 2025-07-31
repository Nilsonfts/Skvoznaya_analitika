#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы calculations.py и config.py
"""

try:
    import os
    print('✅ Шаг 1: импорт os - ОК')
    
    from dotenv import load_dotenv
    print('✅ Шаг 2: импорт dotenv - ОК')
    
    result = load_dotenv()
    print(f'✅ Шаг 3: загрузка .env - {result}')
    
    bot_token = os.getenv('BOT_TOKEN')
    print(f'✅ Шаг 4: получение BOT_TOKEN - {bot_token[:20] if bot_token else "None"}...')
    
    from config import SEGMENT_CONFIG, LTV_CONFIG, CHANNEL_COSTS
    print(f'✅ Шаг 5: импорт config - SEGMENT_CONFIG имеет {len(SEGMENT_CONFIG)} элементов')
    print(f'   LTV_CONFIG: {LTV_CONFIG}')
    print(f'   CHANNEL_COSTS keys: {list(CHANNEL_COSTS.keys())[:5]}...')
    
    from utils.calculations import (
        calculate_cac, calculate_ltv, determine_client_segment,
        calculate_roi, calculate_conversion, calculate_channel_rating
    )
    print('✅ Шаг 6: импорт всех функций из calculations - ОК')
    
    # Тестирование функций
    print('\n🧪 Тестирование функций:')
    
    # Тест CAC
    cac = calculate_cac(50000, 100)
    print(f'   CAC (50000₽, 100 клиентов): {cac}₽')
    
    # Тест LTV
    ltv = calculate_ltv(5000, 3, [4500, 5500, 4800])
    print(f'   LTV (средний чек 5000₽, визиты [4500, 5500, 4800]): {ltv}₽')
    
    # Тест сегментации
    segment = determine_client_segment(4, 20000, [4500, 5500, 4800, 6200])
    print(f'   Сегмент (4 визита, суммы [4500, 5500, 4800, 6200]): {segment}')
    
    # Тест ROI
    roi = calculate_roi(120000, 50000)
    print(f'   ROI (выручка 120000₽, затраты 50000₽): {roi:.1%}')
    
    # Тест конверсии
    conversion = calculate_conversion(25, 100)
    print(f'   Конверсия (25 клиентов из 100 лидов): {conversion:.1%}')
    
    # Тест рейтинга канала
    rating = calculate_channel_rating(1.4, 0.25, 2000)
    print(f'   Рейтинг канала (ROI: 140%, конверсия: 25%, CAC: 2000₽): {rating:.1f}/5.0')
    
    print('\n🎉 Все тесты прошли успешно!')
    
except Exception as e:
    print(f'❌ Ошибка: {e}')
    import traceback
    traceback.print_exc()
