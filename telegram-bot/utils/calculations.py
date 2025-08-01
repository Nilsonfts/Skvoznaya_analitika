"""
Функции для расчета маркетинговых метрик
"""

from typing import Union, List
from config import SEGMENT_CONFIG, LTV_CONFIG, CHANNEL_COSTS

def calculate_cac(channel_cost: float, clients_count: int) -> float:
    """
    Расчет CAC (Customer Acquisition Cost) - стоимость привлечения клиента
    
    Args:
        channel_cost: Расходы на канал в месяц
        clients_count: Количество клиентов из канала
    
    Returns:
        CAC в рублях
    """
    if clients_count == 0:
        return 0.0
    
    return channel_cost / clients_count

def calculate_ltv(avg_check: float, visits_count: int, visit_amounts: List[float] = None) -> float:
    """
    Расчет LTV клиента на основе суммы визитов или среднего чека
    
    Args:
        avg_check: Средний чек клиента
        visits_count: Количество визитов
        visit_amounts: Список сумм по каждому визиту (опционально)
    
    Returns:
        LTV клиента ограниченный 6 визитами в год
    """
    if not avg_check and not visit_amounts:
        return 0.0
    
    # Если есть детализация по визитам, используем её
    if visit_amounts:
        # Ограничиваем до 6 визитов в год
        limited_amounts = visit_amounts[:6]
        return sum(limited_amounts)
    
    # Иначе используем средний чек с ограничением до 6 визитов
    max_visits = min(visits_count, 6)
    return avg_check * max_visits


def determine_client_segment(visits_count: int, total_revenue: float, visit_amounts: List[float] = None) -> str:
    """
    Определение сегмента клиента на основе его активности и дохода
    
    Args:
        visits_count: Количество визитов
        total_revenue: Общий доход от клиента
        visit_amounts: Список сумм по каждому визиту (опционально)
    
    Returns:
        Сегмент клиента
    """
    if visits_count == 0:
        return "Потенциальный"
    
    # Используем суммы визитов для более точного анализа
    if visit_amounts:
        # Анализируем активность клиента
        recent_visits = visit_amounts[:3]  # Последние 3 визита
        avg_recent_check = sum(recent_visits) / len(recent_visits) if recent_visits else 0
        
        # VIP клиенты (высокий средний чек или много визитов)
        if avg_recent_check > 8000 or visits_count >= 5:
            return "VIP"
        
        # Постоянные клиенты (регулярные визиты)
        if visits_count >= 3 and avg_recent_check > 3000:
            return "Постоянный"
        
        # Активные клиенты (несколько визитов)
        if visits_count >= 2:
            return "Активный"
        
        # Новые клиенты
        return "Новый"
    
    # Fallback на старую логику если нет детализации по визитам
    avg_check = total_revenue / visits_count if visits_count > 0 else 0
    
    if visits_count >= 5 or avg_check > 8000:
        return "VIP"
    elif visits_count >= 3 and avg_check > 3000:
        return "Постоянный"
    elif visits_count >= 2:
        return "Активный"
    else:
        return "Новый"

def calculate_roi(revenue: float, cost: float) -> float:
    """
    Расчет ROI (Return on Investment) - возврат инвестиций
    
    Args:
        revenue: Выручка
        cost: Затраты
    
    Returns:
        ROI в процентах (например, 0.5 = 50%)
    """
    if cost == 0:
        return 100.0 if revenue > 0 else 0.0
    
    roi = ((revenue - cost) / cost)
    return roi

def calculate_conversion(clients: int, leads: int) -> float:
    """
    Расчет конверсии из лидов в клиенты
    
    Args:
        clients: Количество клиентов
        leads: Количество лидов
    
    Returns:
        Конверсия в процентах (например, 0.15 = 15%)
    """
    if leads == 0:
        return 0.0
    
    return clients / leads

def calculate_channel_rating(roi: float, conversion: float, cac: float) -> float:
    """
    Расчет рейтинга канала по шкале от 1 до 5 звезд
    
    Args:
        roi: ROI канала в процентах
        conversion: Конверсия канала в процентах
        cac: CAC канала в рублях
    
    Returns:
        Рейтинг от 1.0 до 5.0
    """
    # Весовые коэффициенты для метрик
    roi_weight = 0.5
    conversion_weight = 0.3
    cac_weight = 0.2
    
    # Нормализация ROI (от -100% до 200%)
    roi_score = max(0, min(5, (roi + 1) * 2.5))  # ROI 0% = 2.5, ROI 100% = 5.0
    
    # Нормализация конверсии (от 0% до 50%)
    conversion_score = max(0, min(5, conversion * 10))  # 50% конверсия = 5.0
    
    # Нормализация CAC (инвертированная - чем меньше, тем лучше)
    # Предполагаем, что CAC до 10000 руб - отлично, свыше 50000 - плохо
    if cac == 0:
        cac_score = 5.0
    elif cac <= 10000:
        cac_score = 5.0
    elif cac >= 50000:
        cac_score = 1.0
    else:
        cac_score = 5.0 - ((cac - 10000) / 40000) * 4  # Линейная шкала
    
    # Итоговый рейтинг
    rating = (roi_score * roi_weight + 
              conversion_score * conversion_weight + 
              cac_score * cac_weight)
    
    return max(1.0, min(5.0, rating))

def calculate_payback_period(cac: float, avg_check: float) -> float:
    """
    Расчет периода окупаемости в количестве визитов
    
    Args:
        cac: Стоимость привлечения клиента
        avg_check: Средний чек
    
    Returns:
        Количество визитов для окупаемости
    """
    if avg_check == 0:
        return float('inf')
    
    return cac / avg_check

def calculate_monthly_growth_rate(current_value: float, previous_value: float) -> float:
    """
    Расчет темпа роста за месяц
    
    Args:
        current_value: Текущее значение
        previous_value: Предыдущее значение
    
    Returns:
        Темп роста в процентах
    """
    if previous_value == 0:
        return 100.0 if current_value > 0 else 0.0
    
    return ((current_value - previous_value) / previous_value)

def calculate_customer_lifetime_months(first_visit_date: str, last_visit_date: str) -> int:
    """
    Расчет срока жизни клиента в месяцах
    
    Args:
        first_visit_date: Дата первого визита (YYYY-MM-DD)
        last_visit_date: Дата последнего визита (YYYY-MM-DD)
    
    Returns:
        Количество месяцев между визитами
    """
    try:
        from datetime import datetime
        
        first_date = datetime.strptime(first_visit_date, '%Y-%m-%d')
        last_date = datetime.strptime(last_visit_date, '%Y-%m-%d')
        
        # Разница в месяцах
        months_diff = (last_date.year - first_date.year) * 12 + (last_date.month - first_date.month)
        return max(1, months_diff)  # Минимум 1 месяц
        
    except (ValueError, TypeError):
        return 1

def calculate_channel_efficiency_score(channel_data: dict) -> float:
    """
    Расчет общего индекса эффективности канала
    
    Args:
        channel_data: Словарь с данными канала (roi, conversion, cac, ltv)
    
    Returns:
        Индекс эффективности от 0 до 100
    """
    roi = channel_data.get('roi', 0)
    conversion = channel_data.get('conversion', 0)
    cac = channel_data.get('cac', 0)
    ltv = channel_data.get('ltv', 0)
    
    # Компоненты индекса
    roi_component = max(0, min(40, (roi + 1) * 20))  # Максимум 40 баллов
    conversion_component = max(0, min(30, conversion * 60))  # Максимум 30 баллов
    
    # CAC/LTV соотношение (чем больше LTV к CAC, тем лучше)
    if cac > 0 and ltv > 0:
        ltv_cac_ratio = ltv / cac
        ltv_component = max(0, min(30, ltv_cac_ratio * 10))  # Максимум 30 баллов
    else:
        ltv_component = 0
    
    efficiency_score = roi_component + conversion_component + ltv_component
    return min(100, efficiency_score)

def calculate_market_share(channel_revenue: float, total_revenue: float) -> float:
    """
    Расчет доли канала в общей выручке
    
    Args:
        channel_revenue: Выручка канала
        total_revenue: Общая выручка
    
    Returns:
        Доля в процентах (например, 0.25 = 25%)
    """
    if total_revenue == 0:
        return 0.0
    
    return channel_revenue / total_revenue

def calculate_customer_acquisition_funnel(impressions: int, clicks: int, 
                                        leads: int, clients: int) -> dict:
    """
    Расчет воронки привлечения клиентов
    
    Args:
        impressions: Показы
        clicks: Клики
        leads: Лиды
        clients: Клиенты
    
    Returns:
        Словарь с метриками воронки
    """
    ctr = clicks / impressions if impressions > 0 else 0  # Click-through rate
    lead_conversion = leads / clicks if clicks > 0 else 0  # Конверсия в лиды
    client_conversion = clients / leads if leads > 0 else 0  # Конверсия в клиенты
    overall_conversion = clients / impressions if impressions > 0 else 0  # Общая конверсия
    
    return {
        'ctr': ctr,
        'lead_conversion': lead_conversion,
        'client_conversion': client_conversion,
        'overall_conversion': overall_conversion,
        'impressions': impressions,
        'clicks': clicks,
        'leads': leads,
        'clients': clients
    }

def calculate_seasonal_coefficient(month: int) -> float:
    """
    Расчет сезонного коэффициента для караоке-рюмочной "Евгенич"
    
    Args:
        month: Номер месяца (1-12)
    
    Returns:
        Сезонный коэффициент (1.0 = средний уровень)
    """
    # Сезонность для караоке-рюмочной (развлекательный бизнес)
    seasonal_coefficients = {
        1: 1.0,   # Январь - возвращение к обычному ритму
        2: 1.1,   # Февраль - День Святого Валентина, романтические вечера
        3: 1.1,   # Март - 8 марта, корпоративы
        4: 1.2,   # Апрель - весенние праздники, дни рождения
        5: 1.2,   # Май - майские праздники, свадебный сезон
        6: 0.9,   # Июнь - начало отпусков, дачный сезон
        7: 0.9,   # Июль - отпуска, дачи
        8: 0.9,   # Август - отпуска, конец лета
        9: 1.15,  # Сентябрь - возвращение из отпусков, корпоративы
        10: 1.15, # Октябрь - осенние мероприятия
        11: 1.2,  # Ноябрь - подготовка к новогодним корпоративам
        12: 1.5   # Декабрь - пик новогодних корпоративов и праздников
    }
    
    return seasonal_coefficients.get(month, 1.0)
