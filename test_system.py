#!/usr/bin/env python3
"""
Тестовый скрипт для проверки обновлённой системы аналитики
"""

import asyncio
import sys
import traceback
from datetime import datetime

async def test_system():
    """Комплексное тестирование обновлённой системы"""
    
    print("🧪 ТЕСТИРОВАНИЕ ОБНОВЛЁННОЙ СИСТЕМЫ АНАЛИТИКИ")
    print("=" * 50)
    
    tests_passed = 0
    tests_total = 0
    
    # Тест 1: Импорт Analytics Service
    tests_total += 1
    try:
        from services.analytics import AnalyticsService
        analytics = AnalyticsService()
        print("✅ Analytics Service - импорт успешен")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Analytics Service - ошибка импорта: {e}")
    
    # Тест 2: Импорт Visualization Service  
    tests_total += 1
    try:
        from services.visualization import get_visualization_service
        vis = get_visualization_service()
        print("✅ Visualization Service - импорт успешен")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Visualization Service - ошибка импорта: {e}")
    
    # Тест 3: Rate Limiter
    tests_total += 1
    try:
        from utils.rate_limiter import RateLimiter, rate_limit, admin_rate_limit
        limiter = RateLimiter()
        print("✅ Rate Limiter - импорт успешен")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Rate Limiter - ошибка импорта: {e}")
    
    # Тест 4: Error Handler
    tests_total += 1
    try:
        from utils.error_handler import get_error_handler, ErrorMetrics
        handler = get_error_handler()
        metrics = ErrorMetrics()
        print("✅ Error Handler - импорт успешен")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Error Handler - ошибка импорта: {e}")
    
    # Тест 5: Database Service
    tests_total += 1
    try:
        from services.database import DatabaseService
        print("✅ Database Service - импорт успешен")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Database Service - ошибка импорта: {e}")
    
    # Тест 6: Конфигурация
    tests_total += 1
    try:
        from config import USE_POSTGRES, REDIS_URL, EMOJI
        print("✅ Конфигурация - загружена успешно")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Конфигурация - ошибка загрузки: {e}")
    
    # Тест 7: Команды бота
    tests_total += 1
    try:
        from handlers.commands import (
            channels_chart_command, segments_chart_command,
            forecast_command, compare_channels_command, status_command
        )
        print("✅ Новые команды бота - импорт успешен")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Новые команды бота - ошибка импорта: {e}")
    
    # Тест 8: Расчётные функции
    tests_total += 1
    try:
        from utils.calculations import (
            calculate_seasonal_coefficient, calculate_cac,
            calculate_ltv, calculate_roi
        )
        # Тест расчёта сезонного коэффициента для караоке
        coeff_dec = calculate_seasonal_coefficient(12)  # Декабрь
        coeff_jul = calculate_seasonal_coefficient(7)   # Июль
        
        if coeff_dec > 1.3 and coeff_jul < 1.0:  # Проверяем логику караоке-бара
            print("✅ Расчётные функции - работают корректно")
            print(f"   Коэффициент декабря: {coeff_dec:.2f}")
            print(f"   Коэффициент июля: {coeff_jul:.2f}")
            tests_passed += 1
        else:
            print("⚠️ Расчётные функции - возможные проблемы с коэффициентами")
    except Exception as e:
        print(f"❌ Расчётные функции - ошибка: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print(f"✅ Пройдено: {tests_passed}/{tests_total}")
    print(f"📈 Успешность: {tests_passed/tests_total*100:.1f}%")
    
    if tests_passed == tests_total:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Система готова к запуску.")
        return True
    else:
        print("⚠️ Некоторые тесты не пройдены. Требуется диагностика.")
        return False

def test_visualization():
    """Тест создания тестовых графиков"""
    print("\n🎨 ТЕСТ ВИЗУАЛИЗАЦИИ:")
    try:
        from services.visualization import get_visualization_service
        
        vis = get_visualization_service()
        
        # Тестовые данные для каналов
        test_channels = [
            {
                'name': 'Instagram',
                'revenue': 150000,
                'roi': 0.35,
                'conversion_rate': 0.08,
                'cac': 2500
            },
            {
                'name': 'ВКонтакте', 
                'revenue': 120000,
                'roi': 0.28,
                'conversion_rate': 0.06,
                'cac': 3000
            }
        ]
        
        # Попытка создания графика
        chart_buffer = vis.create_channel_performance_chart(test_channels)
        
        if chart_buffer and len(chart_buffer.getvalue()) > 1000:
            print("✅ Графики создаются успешно")
            return True
        else:
            print("❌ Проблемы с созданием графиков")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка тестирования визуализации: {e}")
        return False

async def main():
    """Главная функция тестирования"""
    print(f"🕐 Начало тестирования: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Основные тесты
        system_ok = await test_system()
        
        # Тест визуализации
        viz_ok = test_visualization()
        
        print(f"\n🕐 Завершение тестирования: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if system_ok and viz_ok:
            print("\n🚀 СИСТЕМА ПОЛНОСТЬЮ ГОТОВА К РАБОТЕ!")
            sys.exit(0)
        else:
            print("\n⚠️ Обнаружены проблемы. Проверьте логи выше.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Критическая ошибка тестирования: {e}")
        print("Полный стектрейс:")
        traceback.print_exc()
        sys.exit(2)

if __name__ == '__main__':
    # Запускаем тестирование
    asyncio.run(main())
