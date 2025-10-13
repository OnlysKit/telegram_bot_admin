import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from modules.handlers.start_handler import router as start_router
from modules.handlers.last_handler import router as last_router
from modules.utils.db import creator, ensure_database_exists

# Список токенов ботов - замените на ваши токены
BOT_TOKENS = ['', '']

async def start_bot(token):
    """Запускает один бот с указанным токеном"""
    bot = Bot(token=token, default=DefaultBotProperties(
        parse_mode=ParseMode.HTML, 
        link_preview_is_disabled=True
    ))
    dp = Dispatcher()
    
    # Регистрируем роутеры
    dp.include_router(start_router)
    dp.include_router(last_router)
    
    try:
        await bot.delete_webhook()
        print(f"🤖 Бот запущен: {token[:10]}...")
        await dp.start_polling(bot)
    except Exception as e:
        print(f"❌ Ошибка бота {token[:10]}: {e}")
    finally:
        await bot.session.close()

async def create_tables():
    """Создает необходимые таблицы в базе данных"""
    await ensure_database_exists()
    await creator(table='users', column_types={
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
    })

async def main():
    """Основная функция"""
    # Создаем таблицы
    await create_tables()
    
    # Фильтруем пустые токены
    valid_tokens = [token for token in BOT_TOKENS if token.strip()]
    
    if not valid_tokens:
        print("❌ Нет валидных токенов для запуска!")
        print("📝 Добавьте токены в список BOT_TOKENS")
        return
    
    print(f"🚀 Запуск {len(valid_tokens)} ботов одновременно...")
    
    # Создаем задачи для каждого бота
    tasks = [asyncio.create_task(start_bot(token)) for token in valid_tokens]
    
    try:
        # Запускаем все боты параллельно
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        print("\n⏹️  Получен сигнал остановки. Завершение работы...")
    except Exception as e:
        print(f"💥 Критическая ошибка: {e}")

if __name__ == "__main__":
    print("🤖 Мульти-бот система TableMan")
    print("=" * 40)
    asyncio.run(main())
