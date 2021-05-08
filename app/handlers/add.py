from datetime import datetime

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from app.misc import dp
from app.models import User, Place, Photo
from app.utils.db import store_user_place_photos
from app.utils.gmaps import place_info_from_query, gmaps_input_photo
from app.utils.handlers import show_place_photos, AddModeCB
from app.utils.keyboards import (
    ConfirmCB, MenuCB, back_button, start_keyboard, confirm_cancel_keyboard,
)


class AddManualStates(StatesGroup):
    START = State()
    OBTAIN_TITLE = State()
    OBTAIN_ADDRESS = State()
    OBTAIN_LOCATION = State()


class AddAutoStates(StatesGroup):
    START = State()
    OBTAIN_PLACE = State()


@dp.message_handler(lambda message: not message.get_args(),
                    commands=['add'],
                    state='*')
async def cmd_add(message: types.Message, state: FSMContext):
    await state.reset_state(with_data=False)
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
    await state.reset_state(with_data=False)
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
async def cq_add_manual(query: types.CallbackQuery):
    await AddManualStates.first()
    await query.message.answer('Введите название места')
    await query.answer()


@dp.message_handler(content_types=types.ContentType.LOCATION,
                    state='USER_LOCATION_EXPIRED')
async def request_user_location(message: types.Message, state: FSMContext):
    location = message.location
    user_location = {
        'latitude': location.latitude,
        'longitude': location.longitude,
        'created_at': datetime.utcnow().isoformat(),
    }
    await state.update_data(user_location=user_location)
    await AddAutoStates.first()
    await find_place(message, state)


@dp.message_handler(commands=['add'], state='*')
@dp.message_handler(state=AddAutoStates.START)
async def find_place(message: types.Message, state: FSMContext):
    if message.is_command():
        place_query = message.get_args()
        await AddAutoStates.START.set()
    else:
        place_query = message.text

    data = await state.get_data()
    user_location = data.get('user_location')

    if user_location:
        created_at = datetime.fromisoformat(user_location['created_at'])
        diff = datetime.utcnow() - created_at
        is_expired = diff.days >= 1
    else:
        is_expired = None

    if not user_location or is_expired:
        await state.update_data(place_query=place_query)
        await state.set_state('USER_LOCATION_EXPIRED')
        await message.answer(
            'Для более точного поиска отправьте свою геолокацию'
        )
        return

    user_location.pop('created_at')
    place_query = place_query or (await state.get_data())['place_query']
    place_data = place_info_from_query(place_query, location=user_location)

    if not place_data:
        await state.reset_state(with_data=False)
        await message.answer('Подходящих мест не найдено')
        await message.answer('Выберите действие', reply_markup=start_keyboard)
        return

    gmaps_photo_references = place_data.pop('photo_references')
    await message.answer_venue(
        place_data['latitude'],
        place_data['longitude'],
        place_data['title'],
        place_data['address'],
    )

    in_photos = [
        await gmaps_input_photo(photo)
        for photo in gmaps_photo_references
    ]
    msgs = await show_place_photos(message, in_photos)

    out_photos = []
    for msg in msgs:
        photo = msg.photo[-1]
        out_photos.append({
            'telegram_file_id': photo.file_id,
            'telegram_file_unique_id': photo.file_unique_id,
        })

    await dp.storage.update_data(
        chat=message.chat.id,
        user=message.from_user.id,
        place=place_data,
        photos=out_photos,
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
    place = Place(**data.get('place'))
    photos = [
        Photo(**photo_data)
        for photo_data in data.get('photos')
    ]

    store_user_place_photos(user, place, photos)
    await state.reset_state(with_data=False)
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
    await state.reset_state(with_data=False)
    await query.message.edit_text(
        'Выберите действие', reply_markup=start_keyboard
    )
    await query.answer()


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


@dp.message_handler(lambda message: message.document.mime_base == 'image',
                    content_types=types.ContentType.DOCUMENT,
                    state=AddManualStates.OBTAIN_LOCATION)
async def request_photo_fail(message: types.Message):
    await message.answer(
        'Извините, фото без сжатия не поддерживаются, '
        'отправьте обычную фотографию'
    )


@dp.message_handler(content_types=types.ContentType.PHOTO,
                    state=AddManualStates.OBTAIN_LOCATION)
async def request_photo(message: types.Message, state: FSMContext):
    place_data = await dp.storage.get_data(
        chat=message.chat.id, user=message.from_user.id
    )
    user = User(telegram_user_id=message.from_user.id)
    place = Place(**place_data)
    photo = message.photo[-1]
    photos = [Photo(
        telegram_file_id=photo.file_id,
        telegram_file_unique_id=photo.file_unique_id,
    )]
    store_user_place_photos(user, place, photos)

    await state.reset_state(with_data=False)
    await message.answer('Место сохранено')
    await message.answer('Выберите действие', reply_markup=start_keyboard)
