import asyncio
from os import getenv
from dotenv import load_dotenv
import logging

from aiogram import Bot, Dispatcher
from bot.handlers import get_routers
from database.database import engine
from database.models import Base

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from bot.utils.scheduler_tasks import check_and_sent
from bot.utils.auto_parser import run_auto_parser

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("VacancyBot.Main")

async def on_startup(bot: Bot):
    logging.info("Синхронизация структуры БД...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logging.info("База данных успешно подготовлена!")

async def main():
    load_dotenv()
    token = getenv("BOT_TOKEN")
    if not token:
        raise ValueError("No token provided")

    dp = Dispatcher()
    bot = Bot(token=token)
    dp.include_routers(*get_routers())
    dp.startup.register(on_startup)

    scheduler = AsyncIOScheduler(timezone="UTC")

    scheduler.add_job(
        run_auto_parser,
        trigger="interval",
        minutes=60
    )

    scheduler.add_job(
        check_and_sent,
        trigger="interval",
        minutes=60,
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