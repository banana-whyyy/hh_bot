from aiogram import F, Router
from bot.keyboards.inline import VacancyResponse
from aiogram.types import CallbackQuery

router = Router()


@router.callback_query(VacancyResponse.filter(F.action == "apply"))
async def handle_apply(callback: CallbackQuery, callback_data: VacancyResponse):
    vacancy_id = callback_data.vacancy_id
    # TODO вызов функции из crud на пометку вакансии в БД
    # await mark_vacancy_as_sent()

    await callback.answer("Ответ принят")
    await callback.message.edit_text(
        text=callback.message.text + "\n\n🟢 <b>Вы откликнулись на эту вакансию!</b>",
        parse_mode="HTML"
    )


@router.callback_query(VacancyResponse.filter(F.action == "cover"))
async def handle_cover(callback: CallbackQuery, callback_data: VacancyResponse):
    await callback.answer("Функция в разработке")
    # vacancy_id = callback_data: vacancy_id


@router.callback_query(VacancyResponse.filter(F.action == "skip"))
async def handle_skip(callback: CallbackQuery, callback_data: VacancyResponse):
    await callback.answer("Вакансия скрыта")
    await callback.message.delete()
    
