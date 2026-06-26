import logging
from sqlalchemy import select

from database.database import async_session_maker
from database.models import User
from database.crud import get_parsed_vacancy
from parser.hh_parse import parse

logger = logging.getLogger("VacancyBot.AutoParser")

async def run_auto_parser():
    logger.info("Запуск автоматического парсера HH.ru...")

    async with async_session_maker() as session:
        result = await session.execute(select(User.search_keyword).where(User.is_active == True).distinct())
        keywords = result.scalars().all()

    if not keywords:
        logger.warning("Нет активных ключевых слов для парсинга")
        return
    
    logger.info(f"Будет выполнено сканирование по запросам: {keywords}")

    for keyword in keywords:
        try:
            logger.info(f"Парсинг вакансий по запросу: '{keyword}'")
            raw_vacancies = await parse(search_text=keyword)

            if not raw_vacancies:
                continue

            async with async_session_maker() as session:
                inserted_count = await get_parsed_vacancy(session, raw_vacancies)
                logger.info(f"Запрос '{keyword}': добавлено {inserted_count} новых вакансий в БД.")
        except Exception as e:
            logger.info(f"Ошибка при парсинге запроса '{keyword}': {e}")

    logger.info("🏁 Автоматический парсер успешно завершил работу.")        
