#!/usr/bin/env python3
"""
Демонстрация новых возможностей обновлённой системы аналитики
"""

import asyncio
import io
from datetime import datetime

def demo_calculations():
    """Демонстрация обновлённых расчётов для караоке-бара"""
    print("🧮 ДЕМОНСТРАЦИЯ РАСЧЁТОВ ДЛЯ КАРАОКЕ-БАРА")
    print("=" * 50)
    
    from utils.calculations import (
        calculate_seasonal_coefficient,
        calculate_cac, calculate_ltv, calculate_roi
    )
    
    # Сезонные коэффициенты для караоке-рюмочной
    months = {
        1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
        5: "Май", 6: "Июнь", 7: "Июль", 8: "Август", 
        9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
    }
    
    print("📅 Сезонные коэффициенты по месяцам:")
    for month, name in months.items():
        coeff = calculate_seasonal_coefficient(month)
        emoji = "🔥" if coeff > 1.1 else "❄️" if coeff < 0.9 else "🌟"
        print(f"   {emoji} {name}: {coeff:.2f}x")
    
    print("\n💰 Пример расчёта метрик:")
    test_cac = calculate_cac(50000, 20)  # 50k потрачено, 20 клиентов
    test_ltv = calculate_ltv(3000, 6)  # средний чек 3k, 6 визитов
    test_roi = calculate_roi(120000, 50000)  # выручка 120k, затраты 50k
    
    print(f"   CAC: {test_cac:.0f} ₽")
    print(f"   LTV: {test_ltv:.0f} ₽") 
    print(f"   ROI: {test_roi:.1%}")
    print(f"   LTV/CAC ratio: {test_ltv/test_cac:.1f}x")

def demo_visualization():
    """Демонстрация системы визуализации"""
    print("\n📊 ДЕМОНСТРАЦИЯ ВИЗУАЛИЗАЦИИ")
    print("=" * 50)
    
    from services.visualization import get_visualization_service
    
    # Тестовые данные каналов
    test_channels = [
        {
            'name': 'Instagram',
            'revenue': 150000,
            'roi': 0.35,
            'conversion_rate': 0.08,
            'cac': 2500,
            'rating': 4.5
        },
        {
            'name': 'ВКонтакте', 
            'revenue': 120000,
            'roi': 0.28,
            'conversion_rate': 0.06,
            'cac': 3000,
            'rating': 4.0
        },
        {
            'name': 'Яндекс.Директ',
            'revenue': 80000,
            'roi': 0.15,
            'conversion_rate': 0.04,
            'cac': 4500,
            'rating': 3.2
        }
    ]
    
    # Тестовые данные сегментов
    test_segments = [
        {
            'segment': 'Корпоративы',
            'clients_count': 45,
            'avg_revenue': 8500,
            'percentage': 35.0
        },
        {
            'segment': 'Дни рождения',
            'clients_count': 38,
            'avg_revenue': 4200,
            'percentage': 30.0
        },
        {
            'segment': 'Семейные мероприятия',
            'clients_count': 25,
            'avg_revenue': 3100,
            'percentage': 20.0
        },
        {
            'segment': 'Романтические вечера',
            'clients_count': 19,
            'avg_revenue': 2800,
            'percentage': 15.0
        }
    ]
    
    # Прогноз выручки
    test_forecast = {
        'historical_avg': 145000,
        'forecast': [
            {
                'month': '2025-02',
                'month_name': 'Февраль 2025',
                'revenue': 135000,
                'seasonal_coefficient': 0.93,
                'growth_factor': 1.02
            },
            {
                'month': '2025-03', 
                'month_name': 'Март 2025',
                'revenue': 152000,
                'seasonal_coefficient': 1.05,
                'growth_factor': 1.04
            },
            {
                'month': '2025-04',
                'month_name': 'Апрель 2025', 
                'revenue': 158000,
                'seasonal_coefficient': 1.09,
                'growth_factor': 1.06
            }
        ],
        'total_forecast': 445000,
        'methodology': 'Историческая средняя × Сезонность × Тренд роста (2%/мес)'
    }
    
    try:
        vis = get_visualization_service()
        
        # Создаём графики
        print("📈 Создание графика каналов...")
        channels_chart = vis.create_channel_performance_chart(test_channels)
        print(f"   ✅ График каналов: {len(channels_chart.getvalue())} байт")
        
        print("🥧 Создание диаграммы сегментов...")
        segments_chart = vis.create_segments_pie_chart(test_segments)
        print(f"   ✅ Диаграмма сегментов: {len(segments_chart.getvalue())} байт")
        
        print("🔮 Создание прогноза...")
        forecast_chart = vis.create_forecast_chart(test_forecast)
        print(f"   ✅ График прогноза: {len(forecast_chart.getvalue())} байт")
        
        print("⚖️ Создание сравнительного графика...")
        comparison_chart = vis.create_comparison_chart(test_channels[0], test_channels[1])
        print(f"   ✅ Сравнительный график: {len(comparison_chart.getvalue())} байт")
        
        print("\n🎉 Все графики созданы успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка создания графиков: {e}")

async def demo_rate_limiter():
    """Демонстрация системы ограничения запросов"""
    print("\n🛡️ ДЕМОНСТРАЦИЯ RATE LIMITER")
    print("=" * 50)
    
    from utils.rate_limiter import RateLimiter
    
    try:
        limiter = RateLimiter()
        
        # Тестируем лимиты для обычного пользователя
        user_id = 12345
        print(f"👤 Тестирование лимитов для пользователя {user_id}:")
        
        for i in range(1, 4):
            is_limited = await limiter.is_rate_limited(user_id, False)
            remaining = await limiter.get_remaining_requests(user_id, False)
            print(f"   Запрос {i}: {'❌ Ограничен' if is_limited else '✅ Разрешён'}, "
                  f"осталось: {remaining}")
            
            if not is_limited:
                await limiter.record_request(user_id, False)
        
        # Тестируем лимиты для админа
        admin_id = 67890
        print(f"\n👑 Тестирование лимитов для админа {admin_id}:")
        
        for i in range(1, 3):
            is_limited = await limiter.is_rate_limited(admin_id, True)
            remaining = await limiter.get_remaining_requests(admin_id, True)
            print(f"   Запрос {i}: {'❌ Ограничен' if is_limited else '✅ Разрешён'}, "
                  f"осталось: {remaining}")
            
            if not is_limited:
                await limiter.record_request(admin_id, True)
        
    except Exception as e:
        print(f"❌ Ошибка тестирования rate limiter: {e}")

def demo_error_handler():
    """Демонстрация системы обработки ошибок"""
    print("\n🔧 ДЕМОНСТРАЦИЯ ERROR HANDLER")
    print("=" * 50)
    
    from utils.error_handler import get_error_handler, get_metrics
    
    try:
        handler = get_error_handler()
        metrics = get_metrics()
        
        # Симулируем несколько запросов
        print("📊 Симуляция запросов:")
        for i in range(5):
            success = i != 2  # Третий запрос будет неуспешным
            metrics.record_request(success)
            status = "✅ Успешно" if success else "❌ Ошибка"
            print(f"   Запрос {i+1}: {status}")
        
        # Получаем статистику
        stats = metrics.get_metrics()
        print(f"\n📈 Статистика:")
        print(f"   Всего запросов: {stats['total_requests']}")
        print(f"   Успешных: {stats['successful_requests']}")
        print(f"   Неудачных: {stats['failed_requests']}")
        print(f"   Процент ошибок: {stats['error_rate']:.1f}%")
        print(f"   Время работы: {stats['uptime']}")
        
        # Статистика ошибок
        error_stats = handler.get_error_stats()
        print(f"\n🔍 Статистика ошибок:")
        print(f"   Всего ошибок: {error_stats['total_errors']}")
        print(f"   Уникальных типов: {error_stats['unique_error_types']}")
        
    except Exception as e:
        print(f"❌ Ошибка тестирования error handler: {e}")

async def main():
    """Главная функция демонстрации"""
    print("🎭 ДЕМОНСТРАЦИЯ КАРАОКЕ-РЮМОЧНОЙ 'ЕВГЕНИЧ СПБ'")
    print("🕐", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("=" * 60)
    
    # Демонстрация всех компонентов
    demo_calculations()
    demo_visualization()
    await demo_rate_limiter()
    demo_error_handler()
    
    print("\n" + "=" * 60)
    print("🎉 ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА!")
    print("🚀 Система готова к работе в караоке-рюмочной 'Евгенич СПБ'")
    print("\n📋 Доступные команды бота:")
    commands = [
        "/report - ежедневный отчёт",
        "/channels_chart - график каналов",
        "/segments_chart - диаграмма сегментов", 
        "/forecast - прогноз выручки",
        "/compare канал1 канал2 - сравнение",
        "/status - статус системы"
    ]
    
    for cmd in commands:
        print(f"   • {cmd}")

if __name__ == '__main__':
    asyncio.run(main())
