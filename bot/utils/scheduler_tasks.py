from aiogram import Bot
import logging
from sqlalchemy import select, update

from database.database import async_session_maker
from database.models import  Vacancy, User
from bot.keyboards.inline import get_vacancy_keyboard

logger = logging.getLogger("VacancyBot.Scheduler")

async def check_and_sent(bot: Bot):
    logger.info("⏰ Планировщик: проверка базы данных на новые вакансии...")

    async with async_session_maker() as session:
        vacancy_query = select(Vacancy).where(Vacancy.is_sent == False).limit(5)
        vacancy_result = await session.execute(vacancy_query)
        unsent_vacancies = vacancy_result.scalars().all()

    if not unsent_vacancies:
        logger.info("Новых вакансий для отправки нет")
        return

    user_query = select(User).where(User.is_active == True)
    user_result = await session.execute(user_query)
    users = user_result.scalars().all()

    if not users:
        logger.warning("Рассылка отменена: в БД нет активных пользователей")
        return
    
    for vacancy in unsent_vacancies:
        text = (
            f"💼 <b>{vacancy.title}</b>\n"
            f"🏢 Компания: {vacancy.company}\n\n"
            f"🔗 <a href='{vacancy.url}'>Открыть на HH.ru</a>"
        )

        for user in users:
            try:
                await bot.send_message(
                    chat_id=user.id,
                    text=text,
                    parse_mode="HTML",
                    reply_markup=get_vacancy_keyboard(vacancy.id)
                )
            except Exception as e:
                logger.error(f"Не удалось отправить сообщение пользователю {user.id}: {e}")
        vacancy.is_sent = True
    
    await session.commit()
    logger.info("Все свежие вакансии успешно разосланы и помечены в БД.")