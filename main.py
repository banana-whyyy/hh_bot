import asyncio
from os import getenv
from dotenv import load_dotenv
import logging

from aiogram import Bot, Dispatcher
from bot.handlers import get_routers

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from bot.utils.scheduler_tasks import check_and_sent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("VacancyBot.Main")


async def main():
    load_dotenv()
    token = getenv("BOT_TOKEN")
    if not token:
        raise ValueError("No token provided")

    dp = Dispatcher()
    bot = Bot(token=token)
    dp.include_routers(*get_routers())

    scheduler = AsyncIOScheduler(timezone="UTC")

    scheduler.add_job(
        check_and_sent,
        trigger="interval",
        seconds=1800,
        kwargs={"bot": bot}
    )

    scheduler.start()
    logger.info("Фоновый планировщик задач успешно запущен")

    logger.info("Бот выходит в онлайн...")

    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Произошла ошибка во время работы бота: {e}")
    finally:
        await bot.session.close()
        logger.info("Бот полностью остановлен.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен пользователем")