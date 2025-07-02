import asyncio
import logging.config
from core.config import MainConfig
from core.bot import dp, bot, register_commands

async def main():
    MainConfig.setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Запуск бота...")

    register_commands(dp)
    
    try:
        await dp.start_polling(bot)
        logger.info("Бот успешно запущен и работает")
    except asyncio.CancelledError:
        logger.info("Работа бота корректно остановлена")
    except Exception as e:
        logger.error(f"Ошибка в работе бота: {e}", exc_info=True)
        raise e
    finally:
        await bot.session.close()
        logger.info("Бот остановлен")

if __name__ == "__main__":
    asyncio.run(main())