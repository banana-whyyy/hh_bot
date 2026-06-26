import logging
from playwright.async_api import async_playwright

logger = logging.getLogger("HH-Responder")

async def apply_to_vacancy(user_data_dir: str, vacancy_id: int, cover_letter: str = None):
    url = f"https://hh.ru/vacancy/{vacancy_id}"
    logger.info(f"Запуск процесса отклика на вакансию {vacancy_id}...")
    
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )

        page = context.pages[0] if context.pages else await context.new_page()
        await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        try:
            await page.goto(url, wait_until="networkidle", timeout=40000)
            await page.wait_for_timeout(2000)

            already_applied = await page.query_selector('[data-qa="vacancy-response-link-top-already-applied"]')
            if already_applied:
                logger.warning(f"Уже откликнулись на {vacancy_id}")
                return "already_applied"
                
            apply_button = await page.query_selector('[data-qa="vacancy-response-link-top"]')
            if not apply_button:
                logger.error("Кнопка отклика вообще не найдена")
                return "button_not_found"
                
            await apply_button.hover()
            await page.wait_for_timeout(400)
            await apply_button.click(force=True, delay=80)
            await page.wait_for_timeout(2500) # Ждем реакции интерфейса
            
            success_check = await page.query_selector('[data-qa="vacancy-response-link-top-already-applied"]')
            if success_check:
                return "success"
                
            logger.info("Обнаружено модальное окно HH. Обрабатываем...")
            
            resume_item = await page.query_selector('.bloko-radio, [data-qa="resume-updater-item"]')
            if resume_item:
                logger.info("Выбираем дефолтное резюме в списке...")
                await resume_item.click()
                await page.wait_for_timeout(500)

            if cover_letter:
                cover_area = await page.query_selector('textarea, [data-qa="vacancy-response-popup-cover-letter-text"]')
                if cover_area:
                    await cover_area.fill(cover_letter)
                    await page.wait_for_timeout(500)
            
            submit_popup_btn = await page.query_selector('[data-qa="vacancy-response-submit-popup"], .bloko-button_kind-primary')
            if submit_popup_btn:
                logger.info("Нажимаем финальную кнопку отправки в модальном окне...")
                await submit_popup_btn.hover()
                await page.wait_for_timeout(300)
                await submit_popup_btn.click(force=True, delay=70)
                await page.wait_for_timeout(3000)
            
            final_check = await page.query_selector('[data-qa="vacancy-response-link-top-already-applied"]')
            if final_check or "already_applied" in page.url:
                logger.info("Отклик успешно доставлен!")
                return "success"
            
            error_guard = await page.query_selector('.bloko-translate-guard')
            if error_guard:
                logger.error(f"Блокировка от HH: {await error_guard.inner_text()}")
                
            return "failed_to_verify"

        except Exception as e:
            logger.error(f"Ошибка выполнения отклика: {e}")
            return "error"
        finally:
            await context.close()