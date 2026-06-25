from aiogram import F, Router
from bot.keyboards.inline import VacancyResponse
from aiogram.types import CallbackQuery

from database.database import async_session_maker
from database.crud import get_user

from aiogram.types import Message
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

router = Router()


class ApplyProcess(StatesGroup):
    waiting_for_custom_cover = State()


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
async def handle_cover(callback: CallbackQuery, callback_data: VacancyResponse, state: ApplyProcess):
    vacancy_id = callback_data.vacancy_id

    async with async_session_maker() as session:
        user = await get_user(session, callback.from_user.id)

    await state.update_data(current_vacancy_id=vacancy_id)

    text = (
        f"📝 <b>Твой текущий шаблон:</b>\n\n<i>{user.cover_letter_template}</i>\n\n"
        f"Если хочешь отправить его <b>без изменений</b>, скопируй его и отправь мне.\n"
        f"Если хочешь изменить — отредактируй прямо сейчас и пришли итоговый текст:"
    )

    await callback.message.answer(text, parse_mode="HTML")
    await state.set_state(ApplyProcess.waiting_for_custom_cover)
    await callback.answer()


@router.message(ApplyProcess.waiting_for_custom_cover)
async def process_custom_cover(message: Message, state: FSMContext):
    user_data = await state.get_data()
    vacancy_id = user_data.get("current_vacancy_id")
    final_cover_text = message.text.strip()

    # TODO: Передаем парсеру команду откликнуться на vacancy_id с текстом final_cover_text
    # await hh_parser.apply_to_vacancy(vacancy_id, final_cover_text)

    await message.answer(
        f"🚀 <b>Отклик отправлен!</b>\n\n"
        f"Сопроводительное письмо для этой вакансии:\n<i>{final_cover_text}</i>", 
        parse_mode="HTML"
    )
    await state.clear()


@router.callback_query(VacancyResponse.filter(F.action == "skip"))
async def handle_skip(callback: CallbackQuery, callback_data: VacancyResponse):
    await callback.answer("Вакансия скрыта")
    await callback.message.delete()
    
