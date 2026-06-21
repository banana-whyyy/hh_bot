import httpx
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def parse():
    url = "https://api.hh.ru/vacancies"

    params = {
        "text": "FastAPI",
        "per_page": 20,
    }

    user_agent = os.getenv("USER_AGENT")
    headers = {
        "User-Agent": user_agent,
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()

            data =response.json()
            vacancies = data.get("items", [])

            parsed_data = []
            for vac in vacancies:
                vac_info = {
                    "hh_id": vac.get("id"),
                    "title": vac.get("name"),
                    "company": vac.get("employer", {}).get("name", "Не указана"),
                    "url": vac.get("alternative_url")
                }
                parsed_data.append(vac_info)
                print(f"[{vac_info['hh_id']}] {vac_info['title']} -> {vac_info['company']}")


        except httpx.HTTPStatusError as exc:
            print(f"Ошибка API. Статус {exc.response.status_code}, при запросе к {exc.request.url}")
            raise
        except httpx.RequestError as exc:
            print(f"Ошибка сети при запросе к {exc.request.url}")
            raise
            
if __name__ == "__main__":
    print("Запуск парсера")
    asyncio.run(parse())