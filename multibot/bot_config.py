# Конфигурация для мульти-бот системы

# Список токенов ваших ботов
# Замените пустые строки на реальные токены
BOT_TOKENS = [
    'YOUR_FIRST_BOT_TOKEN_HERE',  # Токен первого бота
    'YOUR_SECOND_BOT_TOKEN_HERE', # Токен второго бота
    # Добавьте больше токенов по необходимости
]

# Настройки базы данных
DATABASE_CONFIG = {
    'name': 'pfiles/data.db',
    'tables': {
        'users': {
            'user_id': 'INTEGER',
            'topic_id': 'INTEGER', 
            'username': 'TEXT',
            'first_name': 'TEXT',
            'last_name': 'TEXT',
            'source': 'TEXT',
            'is_admin': 'INTEGER',
            'is_moderator': 'INTEGER',
            'banned': 'INTEGER',
            'tariff': 'TEXT',
            'bot_username': 'TEXT',
            'bot_id': 'INTEGER'
        }
    }
}

# Настройки ботов
BOT_SETTINGS = {
    'parse_mode': 'HTML',
    'link_preview_disabled': True,
    'delete_webhook_on_start': True
}

# Настройки логирования
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
}
