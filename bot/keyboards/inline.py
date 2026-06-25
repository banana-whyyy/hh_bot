from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters.callback_data import CallbackData


# apply - отклик, cover - сопроводительное, skip - пропустить
class VacancyResponse(CallbackData, prefix="vac"):
    action: str 
    vacancy_id: int


def get_vacancy_keyboard(vacancy_id: int) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="💼 Откликнуться",
            callback_data=VacancyResponse(action="apply", vacancy_id=vacancy_id).pack()
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="📝 С сопроводительным",
            callback_data=VacancyResponse(action="cover", vacancy_id=vacancy_id).pack()
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="❌ Пропустить",
            callback_data=VacancyResponse(action="skip", vacancy_id=vacancy_id).pack()
        )
    )

    return builder.as_markup()