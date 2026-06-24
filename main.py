import asyncio
from os import getenv
import logging

from aiogram import Bot, Dispatcher
from bot.handlers import get_routers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("VacancyBot.Main")


async def main():
    dp = Dispatcher()
    token = getenv("BOT_TOKEN")
    if not token:
        raise ValueError("No token provided")

    bot = Bot(token=token)
    dp.include_routers(*get_routers())

    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Произошла ошибка во время работы бота: {e}")
    finally:
        # Закрываем сессию бота для чистого выхода
        await bot.session.close()
        logger.info("Бот полностью остановлен.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен пользователем")