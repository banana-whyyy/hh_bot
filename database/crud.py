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