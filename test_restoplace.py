"""
Тест функционала RestoPlace интеграции
"""

import asyncio
import logging
from datetime import datetime
from services.restoplace import RestoPlaceService
from services.reserves_updater import ReservesUpdateService

# Настройка логирования для тестов
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_restoplace_service():
    """Тест сервиса RestoPlace"""
    print("🧪 Тестирование сервиса RestoPlace...")
    
    try:
        async with RestoPlaceService() as rp_service:
            # Тест получения резервов (ограничиваем 1 страницу для теста)
            print("📡 Получение резервов из API...")
            
            reserves = await rp_service.get_reserves(page=1, page_size=10)
            print(f"✅ Получено резервов: {len(reserves.get('data', []))}")
            
            if reserves.get('data'):
                # Тест форматирования данных
                formatted = rp_service.format_reserve_data(reserves['data'][0])
                print(f"✅ Пример отформатированного резерва: {formatted.get('name', 'Без имени')}")
                
                # Тест агрегации гостей
                guests = rp_service.aggregate_guests_data(reserves['data'])
                print(f"✅ Агрегировано гостей: {len(guests)}")
            
    except Exception as e:
        print(f"❌ Ошибка в тесте RestoPlace: {e}")

async def test_reserves_updater():
    """Тест сервиса обновления резервов"""
    print("\n🧪 Тестирование сервиса обновления резервов...")
    
    try:
        updater = ReservesUpdateService()
        
        # Тест с ограниченным количеством дней для быстрого теста
        print("🔄 Запуск обновления данных...")
        stats = await updater.update_reserves_data(days_back=7)
        
        print("📊 Статистика обновления:")
        for key, value in stats.items():
            print(f"  • {key}: {value}")
        
        # Тест генерации сводки
        summary = updater.get_update_summary(stats)
        print(f"\n📋 Сводка:\n{summary}")
        
    except Exception as e:
        print(f"❌ Ошибка в тесте обновления резервов: {e}")

async def test_integration():
    """Комплексный тест интеграции"""
    print("\n🧪 Комплексный тест интеграции...")
    
    try:
        # Проверяем доступность конфигурации
        from config import RESTOPLACE_API_KEY, SPREADSHEET_ID
        
        if not RESTOPLACE_API_KEY:
            print("⚠️  RESTOPLACE_API_KEY не настроен")
            return
        
        if not SPREADSHEET_ID:
            print("⚠️  SPREADSHEET_ID не настроен")
            return
        
        print("✅ Конфигурация найдена")
        
        # Тест подключения к API
        print("🔌 Тестирование подключения к RestoPlace API...")
        async with RestoPlaceService() as rp_service:
            test_data = await rp_service.get_reserves(page=1, page_size=1)
            
            if test_data:
                print("✅ Подключение к RestoPlace API успешно")
            else:
                print("❌ Нет данных от API")
        
    except Exception as e:
        print(f"❌ Ошибка в комплексном тесте: {e}")

async def main():
    """Основная функция тестирования"""
    print("🚀 Запуск тестов интеграции RestoPlace\n")
    
    # Последовательно запускаем тесты
    await test_restoplace_service()
    await test_reserves_updater()
    await test_integration()
    
    print("\n✅ Тестирование завершено!")

if __name__ == "__main__":
    asyncio.run(main())
