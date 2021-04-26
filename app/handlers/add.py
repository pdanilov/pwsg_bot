from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from app.misc import dp
from app.models import User, Place, Photo
from app.utils.db import store_user_place_photos
from app.utils.gmaps import place_info_from_query, gmaps_input_photo
from app.utils.handlers import show_place_photos, AddModeCB
from app.utils.keyboards import (
    ConfirmCB, MenuCB, back_button, start_keyboard, confirm_cancel_keyboard
)


class AddManualStates(StatesGroup):
    START = State()
    OBTAIN_TITLE = State()
    OBTAIN_ADDRESS = State()
    OBTAIN_LOCATION = State()


class AddAutoStates(StatesGroup):
    START = State()
    OBTAIN_PLACE = State()


@dp.message_handler(commands=['add'],
                    content_types=types.ContentType.TEXT,
                    state='*')
async def cmd_add(message: types.Message, state: FSMContext):
    await state.finish()

    if message.get_args():
        await AddAutoStates.first()
        await find_place(message, state)
    else:
        await AddManualStates.first()
        await message.answer('Введите название места')


@dp.callback_query_handler(MenuCB.filter(action='add'))
async def cq_add(query: types.CallbackQuery, state: FSMContext):
    auto_button = types.InlineKeyboardButton(
        'Добавить автоматически',
        callback_data=AddModeCB.new(mode='auto'),
    )
    manual_button = types.InlineKeyboardButton(
        'Добавить вручную',
        callback_data=AddModeCB.new(mode='manual'),
    )
    buttons = [
        [auto_button],
        [manual_button],
        [back_button],
    ]
    keyboard = types.InlineKeyboardMarkup(row_width=1, inline_keyboard=buttons)
    await state.set_state('CHOOSE_ADD_MODE')
    await query.message.edit_text(
        'Выберите режим добавления объекта', reply_markup=keyboard
    )
    await query.answer()


@dp.callback_query_handler(MenuCB.filter(action='back'),
                           state='CHOOSE_ADD_MODE')
async def cq_back_to_main_menu(query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await query.message.edit_text(
        'Выберите действие', reply_markup=start_keyboard
    )
    await query.answer()


@dp.message_handler(content_types=types.ContentType.TEXT,
                    state=AddAutoStates.START)
async def find_place(message: types.Message, state: FSMContext):
    place_query = message.get_args() if message.is_command() else message.text
    place_info = place_info_from_query(place_query)

    if not place_info:
        await state.finish()
        await message.answer('Подходящих мест не найдено')
        await message.answer('Выберите действие', reply_markup=start_keyboard)
        return

    gmaps_photo_references = place_info.pop('photo_references')
    place = Place(**place_info)
    await message.answer_venue(
        place.latitude, place.longitude, place.title, place.address
    )
    in_photos = [
        await gmaps_input_photo(photo)
        for photo in gmaps_photo_references
    ]
    out_photos = await show_place_photos(message, in_photos)
    await dp.storage.update_data(
        chat=message.chat.id,
        user=message.from_user.id,
        place=repr(place),
        photos=repr(out_photos),
    )
    await message.answer(
        'Вы хотите сохранить это место?',
        reply_markup=confirm_cancel_keyboard,
    )
    await AddAutoStates.next()


@dp.callback_query_handler(ConfirmCB.filter(answer='yes'),
                           state=AddAutoStates.OBTAIN_PLACE)
async def cq_confirm_storage(query: types.CallbackQuery, state: FSMContext):
    user_id = query.from_user.id
    data = await dp.storage.get_data(
        chat=query.message.chat.id, user=user_id
    )
    user = User(telegram_user_id=user_id)
    place = eval(data.get('place'))
    photos = eval(data.get('photos'))
    store_user_place_photos(user, place, photos)
    await state.finish()
    await query.message.answer('Место сохранено')
    await query.message.answer(
        'Выберите действие', reply_markup=start_keyboard
    )
    await query.answer()


@dp.callback_query_handler(ConfirmCB.filter(answer='no'),
                           state=AddAutoStates.OBTAIN_PLACE)
async def cq_cancel_storage(
    query: types.CallbackQuery, state: FSMContext
):
    await state.finish()
    await query.message.edit_text(
        'Выберите действие', reply_markup=start_keyboard
    )
    await query.answer()


@dp.callback_query_handler(AddModeCB.filter(mode='auto'),
                           state='CHOOSE_ADD_MODE')
async def cq_add_auto(query: types.CallbackQuery):
    await AddAutoStates.first()
    await query.message.answer('Введите название места или его адрес')
    await query.answer()


@dp.callback_query_handler(AddModeCB.filter(mode='manual'),
                           state='CHOOSE_ADD_MODE')
async def cq_add_manual(callback_query: types.CallbackQuery):
    await AddManualStates.first()
    await callback_query.message.answer('Введите название места')
    await callback_query.answer()


@dp.message_handler(content_types=types.ContentType.TEXT,
                    state=AddManualStates.START)
async def request_title(message: types.Message):
    await dp.storage.update_data(
        chat=message.chat.id,
        user=message.from_user.id,
        title=message.text,
    )
    await message.answer('Добавьте адрес')
    await AddManualStates.next()


@dp.message_handler(content_types=types.ContentType.TEXT,
                    state=AddManualStates.OBTAIN_TITLE)
async def request_address(message: types.Message):
    await dp.storage.update_data(
        chat=message.chat.id,
        user=message.from_user.id,
        address=message.text,
    )
    await message.answer('Добавьте геолокацию')
    await AddManualStates.next()


@dp.message_handler(content_types=types.ContentType.LOCATION,
                    state=AddManualStates.OBTAIN_ADDRESS)
async def request_location(message: types.Message):
    await dp.storage.update_data(
        chat=message.chat.id,
        user=message.from_user.id,
        latitude=message.location.latitude,
        longitude=message.location.longitude,
    )
    await message.answer('Добавьте фотографию')
    await AddManualStates.next()


@dp.message_handler(content_types=types.ContentType.PHOTO,
                    state=AddManualStates.OBTAIN_LOCATION)
async def request_photo(message: types.Message, state: FSMContext):
    kwargs = await dp.storage.get_data(
        chat=message.chat.id, user=message.from_user.id
    )
    user = User(telegram_user_id=message.from_user.id)
    place = Place(**kwargs)
    photo = message.photo[-1]
    photos = [Photo(
        telegram_file_id=photo.file_id,
        telegram_file_unique_id=photo.file_unique_id,
    )]
    store_user_place_photos(user, place, photos)
    await state.finish()
    await message.answer('Место сохранено')
    await message.answer('Выберите действие', reply_markup=start_keyboard)
