from typing import List, Union

from aiogram import types
from aiogram.utils.callback_data import CallbackData

from app.models import Place
from app.utils.keyboards import back_button

ListModeCB = CallbackData("list", "mode")
PlaceCB = CallbackData("place", "id")
AddModeCB = CallbackData("add", "mode")


async def show_place_photos(
    message: types.Message, photos: List[Union[str, types.InputFile]]
) -> List[types.Message]:
    input_media_photos = [types.InputMediaPhoto(in_photo) for in_photo in photos]
    msgs = await message.answer_media_group(input_media_photos) if photos else []
    return msgs


def get_show_places_keyboard(places: List[Place]) -> types.InlineKeyboardMarkup:
    keyboard = types.InlineKeyboardMarkup(row_width=1)

    for place in places:
        button = types.InlineKeyboardButton(
            place.title, callback_data=PlaceCB.new(id=place.id)
        )
        keyboard.row(button)

    keyboard.row(back_button)
    return keyboard
