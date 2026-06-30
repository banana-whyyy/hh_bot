from aiogram import Bot, html
import logging
from sqlalchemy import select, insert

from database.database import async_session_maker
from database.models import Vacancy, User, UserVacancy
from bot.keyboards.inline import get_vacancy_keyboard

logger = logging.getLogger("VacancyBot.Scheduler")

async def check_and_sent(bot: Bot):
    logger.info("⏰ Планировщик: проверка базы данных на новые вакансии...")

    async with async_session_maker() as session:
        user_query = select(User).where(User.search_keyword != None)
        user_result = await session.execute(user_query)
        users = user_result.scalars().all()

        if not users:
            logger.info("Нет пользователей с настроенным поиском.")
            return

        for user in users:
            sent_vacancies_subquery = (
                select(UserVacancy.vacancy_id)
                .where(UserVacancy.user_id == user.id)
            )
            
            vacancy_query = (
                select(Vacancy)
                .where(
                    Vacancy.search_keyword == user.search_keyword,
                    ~Vacancy.id.in_(sent_vacancies_subquery)
                )
                .limit(3) 
            )
            
            vacancies_result = await session.execute(vacancy_query)
            personal_vacancies = vacancies_result.scalars().all()

            if not personal_vacancies:
                continue  # Для этого юзера новых вакансий пока нет, идем к следующему

            logger.info(f"Найдено {len(personal_vacancies)} новых вакансий для пользователя {user.id} по запросу '{user.search_keyword}'")

            for vacancy in personal_vacancies:
                v_title = html.quote(str(vacancy.title))
                v_company = html.quote(str(vacancy.company))
                salary_info = html.quote(vacancy.salary if vacancy.salary else "не указана")
                exp_info = html.quote(vacancy.experience if vacancy.experience else "не указан")

                text = (
                    f"💼 <b>{v_title}</b>\n"
                    f"🏢 Компания: <b>{v_company}</b>\n"
                    f"💰 Зарплата: <code>{salary_info}</code>\n"
                    f"📍 Опыт/Формат: <i>{exp_info}</i>\n\n"
                    f"🔗 <a href='{vacancy.url}'>Открыть на HH.ru</a>"
                )

                try:
                    await bot.send_message(
                        chat_id=user.id,
                        text=text,
                        parse_mode="HTML",
                        reply_markup=get_vacancy_keyboard(vacancy.id)
                    )
                    
                    stmt = insert(UserVacancy).values(user_id=user.id, vacancy_id=vacancy.id)
                    await session.execute(stmt)
                    
                except Exception as e:
                    logger.error(f"Ошибка отправки пользователю {user.id}: {e}")
            
            await session.commit()

    logger.info("⏰ Проверка подписок завершена.")