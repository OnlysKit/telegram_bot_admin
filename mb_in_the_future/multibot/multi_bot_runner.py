import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from modules.handlers.start_handler import router as start_router
from modules.handlers.last_handler import router as last_router
from modules.utils.db import creator, ensure_database_exists

# Список токенов ботов
BOT_TOKENS = ['', '']  # Замените на ваши токены

class MultiBotRunner:
    def __init__(self, tokens):
        self.tokens = tokens
        self.bots = []
        self.dispatchers = []
        
    async def create_bot_and_dispatcher(self, token):
        """Создает бота и диспетчер для одного токена"""
        bot = Bot(token=token, default=DefaultBotProperties(
            parse_mode=ParseMode.HTML, 
            link_preview_is_disabled=True
        ))
        dp = Dispatcher()
        
        # Регистрируем роутеры для каждого бота
        dp.include_router(start_router)
        dp.include_router(last_router)
        
        return bot, dp
    
    async def start_single_bot(self, bot, dp):
        """Запускает один бот"""
        try:
            await bot.delete_webhook()
            print(f"Запуск бота с токеном: {bot.token[:10]}...")
            await dp.start_polling(bot)
        except Exception as e:
            print(f"Ошибка при запуске бота {bot.token[:10]}: {e}")
    
    async def create_tables(self):
        """Создает таблицы в базе данных"""
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
    
    async def run_all_bots(self):
        """Запускает все боты одновременно"""
        # Создаем таблицы
        await self.create_tables()
        
        # Создаем задачи для каждого бота
        tasks = []
        
        for token in self.tokens:
            if token.strip():  # Проверяем, что токен не пустой
                bot, dp = await self.create_bot_and_dispatcher(token)
                self.bots.append(bot)
                self.dispatchers.append(dp)
                
                # Создаем задачу для запуска бота
                task = asyncio.create_task(self.start_single_bot(bot, dp))
                tasks.append(task)
        
        if not tasks:
            print("Нет валидных токенов для запуска ботов!")
            return
        
        print(f"Запуск {len(tasks)} ботов одновременно...")
        
        try:
            # Запускаем все боты параллельно
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            print("\nПолучен сигнал остановки. Завершение работы ботов...")
        except Exception as e:
            print(f"Ошибка при запуске ботов: {e}")
        finally:
            # Закрываем все боты
            await self.close_all_bots()
    
    async def close_all_bots(self):
        """Закрывает все боты"""
        for bot in self.bots:
            try:
                await bot.session.close()
            except Exception as e:
                print(f"Ошибка при закрытии бота: {e}")

async def main():
    """Основная функция для запуска"""
    runner = MultiBotRunner(BOT_TOKENS)
    await runner.run_all_bots()

if __name__ == "__main__":
    # Проверяем, что токены не пустые
    if not any(token.strip() for token in BOT_TOKENS):
        print("Внимание: Все токены в списке BOT_TOKENS пустые!")
        print("Добавьте ваши токены в список BOT_TOKENS в файле multi_bot_runner.py")
    else:
        print("Запуск мульти-бот системы...")
        asyncio.run(main())
