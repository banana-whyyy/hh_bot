import asyncio
import os
import logging
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("HH-Parser")

async def parse(search_text: str):
    url = f"https://hh.ru/search/vacancy?text={search_text}&per_page=20&order_by=publication_time"
    parsed_data = []
    
    logger.info("Запуск браузера Playwright...")
    async with async_playwright() as p:
        user_data_dir = os.path.join(os.getcwd(), "user_data")
        
        context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=True, 
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        
        page = context.pages[0] if context.pages else await context.new_page()
        await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        logger.info(f"Переход на HH.ru: {url}")
        try:
            await page.goto(url, wait_until="networkidle", timeout=60000)
            await page.wait_for_timeout(3000)
            
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2);")
            await page.wait_for_timeout(1500)
            
            cards = await page.query_selector_all('article, [data-qa="vacancy-serp__vacancy"]')
            logger.info(f"Найдено карточек для разбора: {len(cards)}")
            
            seen_ids = set()
            
            for card in cards:
                link_el = await card.query_selector('a[href*="/vacancy/"]')
                if not link_el:
                    continue
                    
                href = await link_el.get_attribute("href")
                clean_url = href.split("?")[0]
                hh_id = clean_url.split("/")[-1]
                
                if hh_id in seen_ids or not hh_id.isdigit():
                    continue
                
                text_loaded = False
                for _ in range(3):
                    card_text = await card.inner_text()
                    if "опыт" in card_text.lower() or any(c in card_text for c in ["₽", "руб", "USD", "опыт", "отклик"]):
                        text_loaded = True
                        break
                    await page.wait_for_timeout(400) 
                
                card_text = await card.inner_text()
                
                title = (await link_el.inner_text()).strip()
                seen_ids.add(hh_id)
                
                company = "Не указана"
                comp_el = await card.query_selector('a[href*="/employer/"]')
                if comp_el:
                    company = (await comp_el.inner_text()).strip()
                
                lines = [line.strip() for line in card_text.split('\n') if line.strip()]
                
                salary = "Не указана"
                currencies = ["₽", "руб", "USD", "$", "₸", "Br", "EUR", "грн", "so'm"]
                for line in lines:
                    if any(curr in line for curr in currencies):
                        if line != title and line != company and any(c.isdigit() for c in line):
                            salary = line
                            break
                
                experience = "Не указан"
                for line in lines:
                    if "опыт" in line.lower() and len(line) < 60:
                        experience = line
                        break
                
                vac_info = {
                    "hh_id": hh_id,
                    "title": title,
                    "company": company,
                    "url": clean_url,
                    "salary": salary,
                    "experience": experience,
                    "search_keyword": search_text
                }
                
                parsed_data.append(vac_info)
                logger.info(f"🎯 Собрано: [{hh_id}] {title} -> {company} | Зп: {salary} | Опыт: {experience}")

        except Exception as e:
            logger.error(f"Ошибка при парсинге: {e}")
        finally:
            await context.close()
            
    return parsed_data

if __name__ == "__main__":
    async def test():
        res = await parse("Python")
        print(f"\nУспешно собрано вакансий: {len(res)}")
    asyncio.run(test())