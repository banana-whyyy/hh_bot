from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from database.database import async_session_maker
from database.crud import register_user, update_user_keyword

router = Router(name="commands")


class SetupSearch(StatesGroup):
    waiting_for_keyword = State()

@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    async with async_session_maker() as session:
        await register_user(
            db=session,
            tg_id=message.from_user.id,
            username=message.from_user.username
        )
    await message.answer(
        f"Привет, {message.from_user.full_name}! 👋\n"
        f"Ты зарегистрирован. По умолчанию я ищу вакансии по запросу <b>FastAPI</b>.\n\n"
        f"🎯 Чтобы изменить поисковый запрос, введи команду: /set_keyword",
        parse_mode="HTML"
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    help_text = (
        "🤖 <b>Справка по командам бота:</b>\n\n"
        "🚀 /start — Запустить бота и зарегистрироваться\n"
        "🎯 /set_keyword — Изменить ключевое слово для поиска\n"
        "❓ /help — Показать это сообщение\n"
    )
    await message.answer(help_text, parse_mode="HTML")


@router.message(Command("set_keyword"))
async def cmd_set_keyword(message: Message, state: FSMContext) -> None:
    await message.answer(
        "Напиши фразу для поиска вакансий на HH.ru.\n"
        "Например: <code>Python Junior</code>, <code>Data Scientist</code> или <code>Django</code>.\n\n"
        "⏳ <i>Ожидаю твой текст...</i>",
        parse_mode="HTML"
    )
    await state.set_state(SetupSearch.waiting_for_keyword)


@router.message(SetupSearch.waiting_for_keyword)
async def proccess_keyword(message: Message, state: FSMContext) -> None:
    user_keyword = message.text.strip()

    if len(user_keyword) < 2:
        await message.answer("⚠️ Запрос слишком короткий. Напиши что-то более конкретное:")
        return

    async with async_session_maker() as session:
        await update_user_keyword(session, message.from_user.id, user_keyword)
    
    await message.answer(
        f"✅ Успешно сохранено!\n"
        f"Теперь я буду искать для тебя: <b>{user_keyword}</b>",
        parse_mode="HTML"
    )

    await state.clear()