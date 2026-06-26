import asyncio
import os
import logging
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("HH-Parser")

async def parse(search_text: str):
    url = f"https://hh.ru/search/vacancy?text={search_text}&per_page=20&order_by=publication_time"
    
    parsed_data = []
    html_content = ""
    
    logger.info("Запуск браузера Playwright...")
    async with async_playwright() as p:
        
        user_data_dir = os.path.join(os.getcwd(), "user_data")

        is_headest = True
        
        context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=is_headest, 
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        
        page = context.pages[0] if context.pages else await context.new_page()
        
        await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        logger.info(f"Переход на HH.ru по запросу: {search_text}")
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=45000)
            
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 3);")
            await page.wait_for_timeout(2000) 
            
            html_content = await page.content()
            
        except Exception as e:
            logger.error(f"Ошибка при загрузческие страницы: {e}")
        finally:
            await context.close()
            
    if not html_content:
        logger.warning("HTML-контент пуст. Парсинг отменен.")
        return []

    
    soup = BeautifulSoup(html_content, "html.parser")
    
    vacancy_cards = soup.find_all(["div", "article"], class_=lambda x: x and "vacancy" in x.lower())
    
    if not vacancy_cards:
        vacancy_cards = soup.find_all(["div", "article"])

    seen_ids = set()
    
    for card in vacancy_cards:
        link_tag = card.find("a", href=lambda h: h and "/vacancy/" in h and "search_field" not in h)
        if not link_tag:
            continue
            
        href = link_tag["href"]
        clean_url = href.split("?")[0]
        hh_id = clean_url.split("/")[-1]
        
        if hh_id in seen_ids or not hh_id.isdigit():
            continue
            
        title = link_tag.text.strip()
        if not title or len(title) < 3: 
            continue
            
        seen_ids.add(hh_id)

        company = "Не указана"
        employer_tag = card.find("a", href=lambda h: h and "/employer/" in h)
        if employer_tag:
            company = employer_tag.text.strip()

        # Ищем зарплату (на HH она часто выделяется тегом со специальным data-qa)
        salary_tag = card.find(attrs={"data-qa": "vacancy-serp__vacancy-compensation"}) or card.find(class_=lambda x: x and "compensation" in x.lower())
        salary = salary_tag.text.strip() if salary_tag else "Не указана"

        # Ищем опыт/формат работы
        exp_tag = card.find(attrs={"data-qa": "vacancy-serp__vacancy-work-experience"}) or card.find(class_=lambda x: x and "experience" in x.lower())
        experience = exp_tag.text.strip() if exp_tag else "Не указан"

        # Краткое описание / Обязанности
        snippet_tag = card.find(attrs={"data-qa": "vacancy-serp__vacancy_snippet_responsibility"}) or card.find(class_=lambda x: x and "snippet" in x.lower())
        description = snippet_tag.text.strip() if snippet_tag else "Описания нет."

        vac_info = {
            "hh_id": hh_id,
            "title": title,
            "company": company,
            "url": clean_url,
            "salary": salary,          
            "experience": experience,  
            "description": description 
        }
        parsed_data.append(vac_info)
        logger.info(f"Найдена вакансия: [{hh_id}] {title} -> {company} | {salary}")
            
    logger.info(f"Скрипт успешно собрал вакансий: {len(parsed_data)}")
    return parsed_data

if __name__ == "__main__":
    from database.database import async_session_maker 
    from database.crud import get_parsed_vacancy      

    async def test_pipeline():
        search_keyword = "FastAPI"
        logger.info(f"--- ШАГ 1: Запуск парсера по ключу {search_keyword} ---")
        
        raw_vacancies = await parse(search_text=search_keyword)
        
        if not raw_vacancies:
            logger.warning("Парсер вернул пустой список. Тест БД отменен.")
            return

        logger.info(f"--- ШАГ 2: Сохранение в базу данных (Всего найдено: {len(raw_vacancies)}) ---")
        
        async with async_session_maker() as session:
            inserted_count = await get_parsed_vacancy(session, raw_vacancies)
            logger.info(f"Успешно добавлено НОВЫХ вакансий в БД: {inserted_count}")

    asyncio.run(test_pipeline())