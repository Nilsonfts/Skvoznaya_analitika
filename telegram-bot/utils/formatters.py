"""
Функции для форматирования данных и очистки
"""

import re
from typing import Union, Optional
from datetime import datetime

def format_currency(amount: Union[int, float], currency: str = '₽') -> str:
    """
    Форматирование денежных сумм
    
    Args:
        amount: Сумма
        currency: Валюта (по умолчанию рубли)
    
    Returns:
        Отформатированная строка с валютой
    """
    if amount == 0:
        return f"0 {currency}"
    
    # Форматирование с разделителями тысяч
    formatted = f"{amount:,.0f}".replace(',', ' ')
    return f"{formatted} {currency}"

def format_percentage(value: Union[int, float], decimal_places: int = 1) -> str:
    """
    Форматирование процентов
    
    Args:
        value: Значение (например, 0.15 для 15%)
        decimal_places: Количество знаков после запятой
    
    Returns:
        Отформатированная строка с процентами
    """
    percentage = value * 100
    return f"{percentage:.{decimal_places}f}%"

def format_number(value: Union[int, float], decimal_places: int = 0) -> str:
    """
    Форматирование чисел с разделителями тысяч
    
    Args:
        value: Число для форматирования
        decimal_places: Количество знаков после запятой
    
    Returns:
        Отформатированная строка
    """
    if decimal_places == 0:
        formatted = f"{value:,.0f}"
    else:
        formatted = f"{value:,.{decimal_places}f}"
    
    return formatted.replace(',', ' ')

def clean_phone(phone: str) -> str:
    """
    Очистка номера телефона от лишних символов
    
    Args:
        phone: Исходный номер телефона
    
    Returns:
        Очищенный номер (только цифры)
    """
    if not phone:
        return ""
    
    # Удаляем все символы кроме цифр
    cleaned = re.sub(r'[^\d]', '', str(phone))
    
    # Убираем ведущую 8 или 7 для российских номеров
    if cleaned.startswith('8') and len(cleaned) == 11:
        cleaned = '7' + cleaned[1:]
    elif cleaned.startswith('7') and len(cleaned) == 11:
        pass  # Оставляем как есть
    
    return cleaned

def normalize_email(email: str) -> str:
    """
    Нормализация email адреса
    
    Args:
        email: Исходный email
    
    Returns:
        Нормализованный email в нижнем регистре
    """
    if not email:
        return ""
    
    # Приводим к нижнему регистру и убираем пробелы
    normalized = str(email).lower().strip()
    
    # Простая валидация email
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(email_pattern, normalized):
        return normalized
    
    return ""

def format_date(date_input: Union[str, datetime], output_format: str = '%Y-%m-%d %H:%M:%S') -> str:
    """
    Форматирование даты в единый формат
    
    Args:
        date_input: Дата в различных форматах
        output_format: Желаемый формат вывода
    
    Returns:
        Отформатированная дата или пустая строка при ошибке
    """
    if not date_input:
        return ""
    
    # Если уже datetime объект
    if isinstance(date_input, datetime):
        return date_input.strftime(output_format)
    
    # Список возможных форматов входных данных
    input_formats = [
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d',
        '%d.%m.%Y %H:%M:%S',
        '%d.%m.%Y',
        '%d/%m/%Y %H:%M:%S',
        '%d/%m/%Y',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%SZ'
    ]
    
    date_str = str(date_input).strip()
    
    for fmt in input_formats:
        try:
            parsed_date = datetime.strptime(date_str, fmt)
            return parsed_date.strftime(output_format)
        except ValueError:
            continue
    
    # Если не удалось распарсить, возвращаем как есть
    return date_str

def format_duration(seconds: int) -> str:
    """
    Форматирование продолжительности в читаемый вид
    
    Args:
        seconds: Продолжительность в секундах
    
    Returns:
        Отформатированная строка (например, "2м 30с")
    """
    if seconds < 60:
        return f"{seconds}с"
    
    minutes = seconds // 60
    remaining_seconds = seconds % 60
    
    if minutes < 60:
        if remaining_seconds > 0:
            return f"{minutes}м {remaining_seconds}с"
        else:
            return f"{minutes}м"
    
    hours = minutes // 60
    remaining_minutes = minutes % 60
    
    if remaining_minutes > 0:
        return f"{hours}ч {remaining_minutes}м"
    else:
        return f"{hours}ч"

def format_rating_stars(rating: float, max_stars: int = 5) -> str:
    """
    Форматирование рейтинга в виде звезд
    
    Args:
        rating: Рейтинг (например, 4.2)
        max_stars: Максимальное количество звезд
    
    Returns:
        Строка со звездами
    """
    full_stars = int(rating)
    half_star = 1 if (rating - full_stars) >= 0.5 else 0
    empty_stars = max_stars - full_stars - half_star
    
    stars = "★" * full_stars
    if half_star:
        stars += "☆"
    stars += "☆" * empty_stars
    
    return stars

def format_change_indicator(current: float, previous: float) -> str:
    """
    Форматирование индикатора изменения с emoji
    
    Args:
        current: Текущее значение
        previous: Предыдущее значение
    
    Returns:
        Строка с индикатором изменения
    """
    if previous == 0:
        if current > 0:
            return "📈 Рост"
        else:
            return "➖ Без изменений"
    
    change = (current - previous) / previous
    change_percent = abs(change) * 100
    
    if change > 0.05:  # Рост более 5%
        return f"📈 +{change_percent:.1f}%"
    elif change < -0.05:  # Снижение более 5%
        return f"📉 -{change_percent:.1f}%"
    else:  # Изменение менее 5%
        return f"➖ {change_percent:.1f}%"

def format_status_emoji(value: float, thresholds: dict) -> str:
    """
    Форматирование статуса с помощью emoji на основе пороговых значений
    
    Args:
        value: Значение для оценки
        thresholds: Словарь с пороговыми значениями {'good': 0.8, 'ok': 0.5}
    
    Returns:
        Emoji индикатор статуса
    """
    good_threshold = thresholds.get('good', 0.8)
    ok_threshold = thresholds.get('ok', 0.5)
    
    if value >= good_threshold:
        return "🟢"  # Зеленый - хорошо
    elif value >= ok_threshold:
        return "🟡"  # Желтый - нормально
    else:
        return "🔴"  # Красный - плохо

def truncate_text(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """
    Обрезка текста до указанной длины
    
    Args:
        text: Исходный текст
        max_length: Максимальная длина
        suffix: Суффикс для обрезанного текста
    
    Returns:
        Обрезанный текст
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def clean_utm_parameter(utm_value: str) -> str:
    """
    Очистка UTM параметров
    
    Args:
        utm_value: Значение UTM параметра
    
    Returns:
        Очищенное значение
    """
    if not utm_value:
        return ""
    
    # Убираем пробелы и приводим к нижнему регистру
    cleaned = str(utm_value).strip().lower()
    
    # Убираем служебные символы
    cleaned = re.sub(r'[^\w\-_.]', '', cleaned)
    
    return cleaned

def format_table_row(data: list, widths: list, separator: str = " | ") -> str:
    """
    Форматирование строки таблицы с выравниванием колонок
    
    Args:
        data: Данные для строки
        widths: Ширина каждой колонки
        separator: Разделитель между колонками
    
    Returns:
        Отформатированная строка таблицы
    """
    formatted_cells = []
    
    for i, (cell, width) in enumerate(zip(data, widths)):
        cell_str = str(cell)
        if len(cell_str) > width:
            cell_str = cell_str[:width-3] + "..."
        formatted_cells.append(cell_str.ljust(width))
    
    return separator.join(formatted_cells)

def format_bytes(bytes_value: int) -> str:
    """
    Форматирование размера в байтах в читаемый вид
    
    Args:
        bytes_value: Размер в байтах
    
    Returns:
        Отформатированная строка (например, "1.5 MB")
    """
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    size = float(bytes_value)
    unit_index = 0
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    else:
        return f"{size:.1f} {units[unit_index]}"

def validate_phone(phone: str) -> bool:
    """
    Валидация номера телефона
    
    Args:
        phone: Номер телефона
    
    Returns:
        True если номер валиден
    """
    cleaned = clean_phone(phone)
    
    # Российский номер должен быть 11 цифр и начинаться с 7
    if len(cleaned) == 11 and cleaned.startswith('7'):
        return True
    
    # Номер без кода страны (10 цифр)
    if len(cleaned) == 10:
        return True
    
    return False

def validate_email(email: str) -> bool:
    """
    Валидация email адреса
    
    Args:
        email: Email адрес
    
    Returns:
        True если email валиден
    """
    if not email:
        return False
    
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, email.strip()))

def escape_markdown(text: str) -> str:
    """
    Экранирование специальных символов для Markdown
    
    Args:
        text: Исходный текст
    
    Returns:
        Экранированный текст
    """
    if not text:
        return ""
    
    # Символы, которые нужно экранировать в Telegram Markdown
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    
    escaped_text = str(text)
    for char in special_chars:
        escaped_text = escaped_text.replace(char, f'\\{char}')
    
    return escaped_text
