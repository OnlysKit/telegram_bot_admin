import asyncio
from modules.bot.bot import bot, dp
from modules.handlers.start_handler import router as start_router
from modules.handlers.last_handler import router as last_router
from modules.handlers.product_sender import router as product_sender
from modules.utils.db import creator, ensure_database_exists

async def main():
    
    await bot.delete_webhook()
    
    # Регистрируем все роутеры
    dp.include_router(start_router)
    dp.include_router(last_router)
    dp.include_router(product_sender)
    # Запускаем бота
    await dp.start_polling(bot)
    
async def create_tables():
    
    # Сначала проверяем и создаем файл базы данных
    await ensure_database_exists()
    # Затем создаем таблицы
    await creator(table='users', column_types={'user_id': 'INTEGER', 'topic_id': 'INTEGER', 'username': 'TEXT',
                                               'first_name': 'TEXT', 'last_name': 'TEXT', 'source': 'TEXT', 
                                               'is_admin': 'INTEGER', 'is_moderator': 'INTEGER', 'banned': 'INTEGER',
                                               'tariff': 'TEXT', 'bot_username': 'TEXT', 'bot_id': 'INTEGER',
                                               })
    await creator(table='purchased', column_types={'user_id': 'INTEGER', 'product_id': 'INTEGER', 'step': 'TEXT', 'paid': 'INTEGER'})

if __name__ == "__main__":
    asyncio.run(create_tables())
    asyncio.run(main())