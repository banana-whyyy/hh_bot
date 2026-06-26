from aiogram import F, Router
from bot.keyboards.inline import VacancyResponse
from aiogram.types import CallbackQuery
import os

from database.database import async_session_maker
from database.crud import get_user
from parser.responder import apply_to_vacancy

from aiogram.types import Message
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

router = Router()

USER_DATA_DIR = os.path.join(os.getcwd(), "user_data")

class ApplyProcess(StatesGroup):
    waiting_for_custom_cover = State()


@router.callback_query(VacancyResponse.filter(F.action == "apply"))
async def handle_apply(callback: CallbackQuery, callback_data: VacancyResponse):
    vacancy_id = callback_data.vacancy_id
    await callback.answer("Запускаю отклик на HH...")
    await callback.message.edit_text(
        text=callback.message.text + "\n\n⏳ <i>Отправка отклика, подождите...</i>",
        parse_mode="HTML"
    )

    result = await apply_to_vacancy(USER_DATA_DIR, vacancy_id, cover_letter=None)

    if result == "success":
        # TODO: вызов на пометку вакансии в БД
        # await mark_vacancy_as_sent(session, vacancy_id)
        status_text = "\n\n🟢 <b>Вы успешно откликнулись на эту вакансию!</b>"
    elif result == "already_applied":
        status_text = "\n\n🟡 <b>Вы уже откликались на эту вакансию ранее!</b>"
    elif result == "phone_only":
        status_text = "\n\n⚠️ <b>Отклик не отправлен: работодатель принимает только звонки.</b>"
    else:
        status_text = "\n\n🔴 <b>Не удалось откликнуться автоматически (возможна капча). Проверь браузер.</b>"

    base_text = callback.message.text.split("\n\n⏳")[0]
    await callback.message.edit_text(
        text=base_text + status_text,
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

    status_msg = await message.answer(
        f"⏳ <b>Отправляю сопроводительное письмо на HH для вакансии {vacancy_id}...</b>",
        parse_mode="HTML"
    )

    result = await apply_to_vacancy(USER_DATA_DIR, vacancy_id, cover_letter=final_cover_text)

    if result == "success":
        await status_msg.edit_text(
            f"🚀 <b>Отклик успешно отправлен!</b>\n\n"
            f"Письмо:\n<i>{final_cover_text}</i>", 
            parse_mode="HTML"
        )
    elif result == "already_applied":
        await status_msg.edit_text("🟡 <b>Вы уже откликались на эту вакансию ранее. Письмо не продублировано.</b>", parse_mode="HTML")
    else:
        await status_msg.edit_text("🔴 <b>Ошибка при отправке сопроводительного. Проверьте логи парсера.</b>", parse_mode="HTML")
        
    await state.clear()


@router.callback_query(VacancyResponse.filter(F.action == "skip"))
async def handle_skip(callback: CallbackQuery, callback_data: VacancyResponse):
    await callback.answer("Вакансия скрыта")
    await callback.message.delete()
    
