#!/usr/bin/env python3
"""
Простой тест функций calculations.py без запуска бота
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_calculations():
    """Тестирование всех функций из calculations.py"""
    
    print("🧪 Тестирование модуля calculations.py")
    print("=" * 50)
    
    try:
        # Импорт констант из config
        from config import SEGMENT_CONFIG, LTV_CONFIG, CHANNEL_COSTS
        print("✅ Константы из config.py загружены:")
        print(f"   - SEGMENT_CONFIG: {list(SEGMENT_CONFIG.keys())}")
        print(f"   - LTV_CONFIG: {LTV_CONFIG}")
        print(f"   - CHANNEL_COSTS: {len(CHANNEL_COSTS)} каналов")
        
        # Импорт функций
        from utils.calculations import (
            calculate_cac,
            calculate_ltv,
            determine_client_segment,
            calculate_roi,
            calculate_conversion,
            calculate_channel_rating,
            calculate_payback_period,
            calculate_monthly_growth_rate,
            calculate_customer_lifetime_months,
            calculate_channel_efficiency_score,
            calculate_market_share,
            calculate_customer_acquisition_funnel,
            calculate_seasonal_coefficient
        )
        print("✅ Все функции из calculations.py импортированы")
        
        print("\n🔍 Тестирование функций:")
        print("-" * 30)
        
        # Тест 1: CAC
        cac = calculate_cac(50000, 100)
        print(f"1. CAC (50000₽, 100 клиентов): {cac}₽")
        assert cac == 500, f"Ожидался CAC=500, получен {cac}"
        
        # Тест 2: LTV
        ltv = calculate_ltv(5000, 3, [4500, 5500, 4800])
        print(f"2. LTV с суммами визитов [4500, 5500, 4800]: {ltv}₽")
        assert ltv == 14800, f"Ожидался LTV=14800, получен {ltv}"
        
        # Тест 3: Сегментация
        segment = determine_client_segment(4, 20000, [4500, 5500, 4800, 6200])
        print(f"3. Сегмент клиента (4 визита, сумма 20000₽): {segment}")
        assert segment in ["VIP", "Постоянный", "Активный", "Новый"], f"Неизвестный сегмент: {segment}"
        
        # Тест 4: ROI
        roi = calculate_roi(120000, 50000)
        print(f"4. ROI (выручка 120000₽, затраты 50000₽): {roi:.1%}")
        assert abs(roi - 1.4) < 0.01, f"Ожидался ROI=1.4, получен {roi}"
        
        # Тест 5: Конверсия
        conversion = calculate_conversion(25, 100)
        print(f"5. Конверсия (25 клиентов из 100 лидов): {conversion:.1%}")
        assert conversion == 0.25, f"Ожидалась конверсия=0.25, получена {conversion}"
        
        # Тест 6: Рейтинг канала
        rating = calculate_channel_rating(1.4, 0.25, 2000)
        print(f"6. Рейтинг канала (ROI: 140%, конверсия: 25%, CAC: 2000₽): {rating:.1f}/5.0")
        assert 1.0 <= rating <= 5.0, f"Рейтинг должен быть от 1 до 5, получен {rating}"
        
        # Тест 7: Период окупаемости
        payback = calculate_payback_period(2000, 1000)
        print(f"7. Период окупаемости (CAC: 2000₽, средний чек: 1000₽): {payback} визитов")
        assert payback == 2.0, f"Ожидался период=2.0, получен {payback}"
        
        # Тест 8: Темп роста
        growth = calculate_monthly_growth_rate(120000, 100000)
        print(f"8. Темп роста (120000₽ vs 100000₽): {growth:.1%}")
        assert growth == 0.2, f"Ожидался рост=0.2, получен {growth}"
        
        # Тест 9: Срок жизни клиента
        lifetime = calculate_customer_lifetime_months("2024-01-01", "2024-06-01")
        print(f"9. Срок жизни клиента (янв-июнь 2024): {lifetime} месяцев")
        assert lifetime == 5, f"Ожидалось 5 месяцев, получено {lifetime}"
        
        # Тест 10: Эффективность канала
        channel_data = {'roi': 1.4, 'conversion': 0.25, 'cac': 2000, 'ltv': 10000}
        efficiency = calculate_channel_efficiency_score(channel_data)
        print(f"10. Индекс эффективности канала: {efficiency:.1f}/100")
        assert 0 <= efficiency <= 100, f"Эффективность должна быть от 0 до 100, получена {efficiency}"
        
        # Тест 11: Доля рынка
        market_share = calculate_market_share(30000, 120000)
        print(f"11. Доля канала в выручке (30000₽ из 120000₽): {market_share:.1%}")
        assert abs(market_share - 0.25) < 0.01, f"Ожидалась доля=0.25, получена {market_share}"
        
        # Тест 12: Воронка конверсии
        funnel = calculate_customer_acquisition_funnel(10000, 500, 100, 25)
        print(f"12. Воронка конверсии (10000→500→100→25):")
        print(f"    CTR: {funnel['ctr']:.1%}, Lead conv: {funnel['lead_conversion']:.1%}")
        assert funnel['clients'] == 25, f"Ожидалось 25 клиентов, получено {funnel['clients']}"
        
        # Тест 13: Сезонность
        winter_coeff = calculate_seasonal_coefficient(12)  # Декабрь
        summer_coeff = calculate_seasonal_coefficient(7)   # Июль
        print(f"13. Сезонные коэффициенты: декабрь={winter_coeff}, июль={summer_coeff}")
        assert winter_coeff > summer_coeff, f"Декабрь должен быть активнее июля"
        
        print("\n🎉 Все тесты пройдены успешно!")
        print("✅ Модуль calculations.py работает корректно")
        return True
        
    except Exception as e:
        print(f"\n❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_calculations()
    sys.exit(0 if success else 1)
