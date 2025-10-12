import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from modules.handlers.start_handler import router as start_router
from modules.handlers.last_handler import router as last_router
from modules.utils.db import creator, ensure_database_exists
from bot_config import BOT_TOKENS, DATABASE_CONFIG, BOT_SETTINGS, LOGGING_CONFIG

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, LOGGING_CONFIG['level']),
    format=LOGGING_CONFIG['format']
)
logger = logging.getLogger(__name__)

class AdvancedMultiBotRunner:
    def __init__(self):
        self.bots = []
        self.dispatchers = []
        self.running_tasks = []
        
    async def create_bot_instance(self, token, bot_id):
        """Создает экземпляр бота с уникальным ID"""
        bot = Bot(
            token=token, 
            default=DefaultBotProperties(
                parse_mode=getattr(ParseMode, BOT_SETTINGS['parse_mode']),
                link_preview_is_disabled=BOT_SETTINGS['link_preview_disabled']
            )
        )
        
        dp = Dispatcher()
        
        # Регистрируем роутеры
        dp.include_router(start_router)
        dp.include_router(last_router)
        
        logger.info(f"Создан бот #{bot_id} с токеном: {token[:10]}...")
        return bot, dp
    
    async def start_single_bot(self, bot, dp, bot_id):
        """Запускает один бот с обработкой ошибок"""
        try:
            if BOT_SETTINGS['delete_webhook_on_start']:
                await bot.delete_webhook()
            
            logger.info(f"🚀 Запуск бота #{bot_id}")
            await dp.start_polling(bot)
            
        except asyncio.CancelledError:
            logger.info(f"⏹️  Бот #{bot_id} остановлен")
        except Exception as e:
            logger.error(f"❌ Ошибка в боте #{bot_id}: {e}")
        finally:
            try:
                await bot.session.close()
                logger.info(f"🔒 Сессия бота #{bot_id} закрыта")
            except Exception as e:
                logger.error(f"Ошибка при закрытии сессии бота #{bot_id}: {e}")
    
    async def setup_database(self):
        """Настраивает базу данных"""
        try:
            await ensure_database_exists()
            
            for table_name, columns in DATABASE_CONFIG['tables'].items():
                await creator(table=table_name, column_types=columns)
                logger.info(f"📊 Таблица '{table_name}' готова")
                
        except Exception as e:
            logger.error(f"Ошибка настройки БД: {e}")
            raise
    
    async def run_all_bots(self):
        """Запускает все боты параллельно"""
        # Настраиваем базу данных
        await self.setup_database()
        
        # Фильтруем валидные токены
        valid_tokens = [token for token in BOT_TOKENS if token and token.strip()]
        
        if not valid_tokens:
            logger.error("❌ Нет валидных токенов для запуска!")
            return
        
        logger.info(f"🎯 Запуск {len(valid_tokens)} ботов...")
        
        # Создаем и запускаем ботов
        for i, token in enumerate(valid_tokens, 1):
            try:
                bot, dp = await self.create_bot_instance(token, i)
                self.bots.append(bot)
                self.dispatchers.append(dp)
                
                # Создаем задачу для бота
                task = asyncio.create_task(
                    self.start_single_bot(bot, dp, i),
                    name=f"bot_{i}"
                )
                self.running_tasks.append(task)
                
            except Exception as e:
                logger.error(f"Ошибка создания бота #{i}: {e}")
        
        if not self.running_tasks:
            logger.error("❌ Не удалось создать ни одного бота!")
            return
        
        try:
            # Запускаем все боты параллельно
            await asyncio.gather(*self.running_tasks, return_exceptions=True)
            
        except KeyboardInterrupt:
            logger.info("🛑 Получен сигнал остановки...")
        except Exception as e:
            logger.error(f"💥 Критическая ошибка: {e}")
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Корректное завершение работы всех ботов"""
        logger.info("🔄 Завершение работы ботов...")
        
        # Отменяем все задачи
        for task in self.running_tasks:
            if not task.done():
                task.cancel()
        
        # Ждем завершения всех задач
        if self.running_tasks:
            await asyncio.gather(*self.running_tasks, return_exceptions=True)
        
        logger.info("✅ Все боты остановлены")

async def main():
    """Основная функция"""
    print("🤖 Advanced Multi-Bot System для TableMan")
    print("=" * 50)
    
    runner = AdvancedMultiBotRunner()
    await runner.run_all_bots()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 До свидания!")
    except Exception as e:
        print(f"💥 Фатальная ошибка: {e}")
