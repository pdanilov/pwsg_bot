from aiogram import types
from aiogram.utils.callback_data import CallbackData

ConfirmCB = CallbackData("confirm", "answer")
MenuCB = CallbackData("menu", "action")

confirm_button = types.InlineKeyboardButton(
    "Подтвердить", callback_data=ConfirmCB.new(answer="yes")
)
cancel_button = types.InlineKeyboardButton(
    "Отмена", callback_data=ConfirmCB.new(answer="no")
)

confirm_cancel_keyboard = types.InlineKeyboardMarkup(
    row_width=2, inline_keyboard=[[confirm_button, cancel_button]]
)

add_button = types.InlineKeyboardButton(
    "Добавить место", callback_data=MenuCB.new(action="add")
)
list_button = types.InlineKeyboardButton(
    "Список сохраненных мест", callback_data=MenuCB.new(action="list")
)
reset_button = types.InlineKeyboardButton(
    "Удалить все сохраненные места", callback_data=MenuCB.new(action="reset")
)

start_keyboard = types.InlineKeyboardMarkup(
    row_width=1, inline_keyboard=[[add_button], [list_button], [reset_button]]
)

back_button = types.InlineKeyboardButton(
    "« Назад", callback_data=MenuCB.new(action="back")
)
