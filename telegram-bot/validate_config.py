#!/usr/bin/env python3
"""
Валидация конфигурации Telegram-бота
Проверяет наличие всех необходимых переменных окружения и их корректность
"""

import os
import sys
import json
from typing import List, Tuple

def check_required_env_vars() -> List[Tuple[str, str, bool]]:
    """
    Проверка обязательных переменных окружения
    
    Returns:
        Список кортежей (переменная, описание, найдена)
    """
    required_vars = [
        ('BOT_TOKEN', 'Токен Telegram бота', False),
        ('GOOGLE_CREDENTIALS_JSON', 'JSON ключ Google API или путь к файлу', False),
        ('SPREADSHEET_ID', 'ID основной Google таблицы', False),
    ]
    
    results = []
    for var_name, description, _ in required_vars:
        # Проверяем основную переменную и альтернативные названия
        value = None
        if var_name == 'BOT_TOKEN':
            value = os.getenv('BOT_TOKEN') or os.getenv('TELEGRAM_TOKEN')
        elif var_name == 'GOOGLE_CREDENTIALS_JSON':
            value = os.getenv('GOOGLE_CREDENTIALS_JSON') or os.getenv('GOOGLE_CREDENTIALS_FILE')
        else:
            value = os.getenv(var_name)
        
        is_found = bool(value and value.strip())
        results.append((var_name, description, is_found))
    
    return results

def check_optional_env_vars() -> List[Tuple[str, str, bool]]:
    """
    Проверка опциональных переменных окружения
    
    Returns:
        Список кортежей (переменная, описание, найдена)
    """
    optional_vars = [
        ('ADMIN_IDS', 'ID администраторов Telegram'),
        ('REPORT_CHAT_ID', 'ID чатов для автоматических отчётов'),
        ('METRIKA_COUNTER_ID', 'ID счётчика Яндекс.Метрики'),
        ('METRIKA_OAUTH_TOKEN', 'OAuth токен Яндекс.Метрики'),
        ('GA_PROPERTY_ID', 'ID свойства Google Analytics'),
        ('AMOCRM_SHEET_ID', 'ID таблицы AmoCRM'),
        ('USE_POSTGRES', 'Использование PostgreSQL'),
        ('DATABASE_URL', 'URL подключения к PostgreSQL'),
        ('REDIS_HOST', 'Хост Redis сервера'),
        ('DEBUG_MODE', 'Режим отладки'),
        ('TIMEZONE', 'Часовой пояс')
    ]
    
    results = []
    for var_name, description in optional_vars:
        value = os.getenv(var_name)
        is_found = bool(value and value.strip())
        results.append((var_name, description, is_found))
    
    return results

def validate_json_credentials() -> Tuple[bool, str]:
    """
    Валидация JSON ключей Google API
    
    Returns:
        Кортеж (валидный, сообщение об ошибке)
    """
    # Проверяем прямой JSON
    json_content = os.getenv('GOOGLE_CREDENTIALS_JSON', '')
    if json_content:
        try:
            credentials = json.loads(json_content)
            required_fields = ['type', 'project_id', 'private_key', 'client_email']
            missing_fields = [field for field in required_fields if field not in credentials]
            
            if missing_fields:
                return False, f"В JSON ключе отсутствуют поля: {', '.join(missing_fields)}"
            
            return True, "JSON ключ валиден"
        except json.JSONDecodeError:
            return False, "Невалидный JSON в GOOGLE_CREDENTIALS_JSON"
    
    # Проверяем файл
    credentials_file = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
    if os.path.exists(credentials_file):
        try:
            with open(credentials_file, 'r') as f:
                credentials = json.load(f)
            
            required_fields = ['type', 'project_id', 'private_key', 'client_email']
            missing_fields = [field for field in required_fields if field not in credentials]
            
            if missing_fields:
                return False, f"В файле {credentials_file} отсутствуют поля: {', '.join(missing_fields)}"
            
            return True, f"Файл {credentials_file} валиден"
        except (json.JSONDecodeError, IOError) as e:
            return False, f"Ошибка чтения файла {credentials_file}: {e}"
    
    return False, "Не найден ни JSON ключ, ни файл с credentials"

def validate_spreadsheet_id() -> Tuple[bool, str]:
    """
    Валидация ID Google таблицы
    
    Returns:
        Кортеж (валидный, сообщение)
    """
    spreadsheet_id = os.getenv('SPREADSHEET_ID', '')
    if not spreadsheet_id:
        return False, "SPREADSHEET_ID не указан"
    
    # Проверяем формат ID (обычно содержит буквы, цифры, дефисы и подчеркивания)
    if len(spreadsheet_id) < 20 or not all(c.isalnum() or c in '-_' for c in spreadsheet_id):
        return False, f"Невалидный формат SPREADSHEET_ID: {spreadsheet_id}"
    
    return True, f"SPREADSHEET_ID выглядит корректно: {spreadsheet_id}"

def validate_telegram_token() -> Tuple[bool, str]:
    """
    Валидация токена Telegram бота
    
    Returns:
        Кортеж (валидный, сообщение)
    """
    token = os.getenv('BOT_TOKEN') or os.getenv('TELEGRAM_TOKEN')
    if not token:
        return False, "BOT_TOKEN не указан"
    
    # Проверяем формат токена (например: 123456789:ABC-DEF1234ghIkl-zyx57W2v1u123ew11)
    if ':' not in token or len(token) < 35:
        return False, f"Невалидный формат BOT_TOKEN"
    
    return True, "BOT_TOKEN выглядит корректно"

def validate_ids(var_name: str, description: str) -> Tuple[bool, str]:
    """
    Валидация списка ID
    
    Args:
        var_name: Название переменной
        description: Описание переменной
        
    Returns:
        Кортеж (валидный, сообщение)
    """
    ids_str = os.getenv(var_name, '')
    if not ids_str:
        return True, f"{description}: не указано (опционально)"
    
    try:
        ids = [x.strip() for x in ids_str.split(',') if x.strip()]
        # Проверяем что все ID являются числами (могут быть отрицательными для групп)
        for id_str in ids:
            int(id_str)
        
        return True, f"{description}: найдено {len(ids)} ID"
    except ValueError:
        return False, f"{description}: содержит некорректные ID"

def main():
    """Основная функция валидации"""
    print("🔍 Проверка конфигурации Telegram-бота")
    print("=" * 60)
    
    all_valid = True
    
    # Проверка обязательных переменных
    print("\n📋 Обязательные переменные:")
    required_vars = check_required_env_vars()
    for var_name, description, is_found in required_vars:
        status = "✅" if is_found else "❌"
        print(f"  {status} {var_name}: {description}")
        if not is_found:
            all_valid = False
    
    # Валидация специфических параметров
    print("\n🔧 Валидация параметров:")
    
    # Telegram токен
    token_valid, token_msg = validate_telegram_token()
    status = "✅" if token_valid else "❌"
    print(f"  {status} Telegram Token: {token_msg}")
    if not token_valid:
        all_valid = False
    
    # Google credentials
    creds_valid, creds_msg = validate_json_credentials()
    status = "✅" if creds_valid else "❌"
    print(f"  {status} Google Credentials: {creds_msg}")
    if not creds_valid:
        all_valid = False
    
    # Spreadsheet ID
    sheet_valid, sheet_msg = validate_spreadsheet_id()
    status = "✅" if sheet_valid else "❌"
    print(f"  {status} Spreadsheet ID: {sheet_msg}")
    if not sheet_valid:
        all_valid = False
    
    # ID списки
    for var_name, description in [('ADMIN_IDS', 'Admin IDs'), ('REPORT_CHAT_ID', 'Report Chat IDs')]:
        ids_valid, ids_msg = validate_ids(var_name, description)
        status = "✅" if ids_valid else "⚠️"
        print(f"  {status} {ids_msg}")
        if not ids_valid:
            all_valid = False
    
    # Проверка опциональных переменных
    print("\n📝 Опциональные переменные:")
    optional_vars = check_optional_env_vars()
    for var_name, description, is_found in optional_vars:
        status = "✅" if is_found else "⚪"
        print(f"  {status} {var_name}: {description}")
    
    # Итоговый результат
    print("\n" + "=" * 60)
    if all_valid:
        print("🎉 Конфигурация валидна! Бот готов к запуску.")
        return 0
    else:
        print("❌ Обнаружены ошибки в конфигурации. Исправьте их перед запуском.")
        print("\n💡 Подсказки:")
        print("  1. Скопируйте .env.example в .env")
        print("  2. Заполните обязательные переменные")
        print("  3. Получите токен бота у @BotFather")
        print("  4. Настройте Google API credentials")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
