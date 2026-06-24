from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert

from .models import User, Vacancy

async def get_parsed_vacancy(db: AsyncSession, vacancies_list: list[dict]) -> int:
    if not vacancies_list:
        return 0

    formated_data = []
    for v in vacancies_list:
        formated_data.append({
            "id": v["hh_id"],
            "title": v["title"],
            "company": v["company"],
            "url": v["url"]
        })
    
    stmt = insert(Vacancy).values(formated_data)
    stmt = stmt.on_conflict_do_nothing(index_elements=["id"])

    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount


async def register_user(db: AsyncSession, tg_id: int, username: str | None):
    stmt = insert(User).values(id=tg_id, username=username)
    stmt = stmt.on_conflict_do_nothing(index_elements=["id"])
    await db.execute(stmt)
    await db.commit()


async def get_active_users(db: AsyncSession) -> list[int]:
    result = await db.execute(select(User.id).where(User.is_active == True))
    return list(result.scalars().all())


async def get_new_vacancies(db: AsyncSession) -> list[Vacancy]:
    result = await db.execute(select(Vacancy).where(Vacancy.is_sent == False).order_by(Vacancy.parsed_at.asc()))
    return list(result.scalars().all())


async def mark_vacancy_as_sent(db: AsyncSession, vacancy_id: str):
    stmt = update(Vacancy).where(Vacancy.id == vacancy_id).values(is_sent=True)
    await db.execute(stmt)
    await db.commit()


async def update_user_keyword(db: AsyncSession, tg_id: int, keyword: str):
    await db.execute(update(User).where(User.id == tg_id).values(keyword=keyword))
    await db.commit()
