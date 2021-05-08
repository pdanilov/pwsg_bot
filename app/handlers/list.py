from datetime import datetime

from aiogram import types
from aiogram.dispatcher import FSMContext
from sqlalchemy import desc

from app.misc import dp
from app.models import session, Place, User
from app.utils.gmaps import distances_from_location_to_places
from app.utils.handlers import (
    show_place_photos,
    get_show_places_keyboard,
    ListModeCB,
    PlaceCB,
)
from app.utils.keyboards import MenuCB, start_keyboard, back_button


@dp.message_handler(commands=['list'], state='*')
async def cmd_list(message: types.Message, state: FSMContext):
    await state.reset_state(with_data=False)

    if message.get_args() == 'nearest':
        await state.set_state('LIST_NEAREST')
        await message.answer('Отправьте свою геолокацию')
    else:
        places = (
            session
            .query(Place)
            .select_from(User)
            .join(User.places)
            .filter_by(telegram_user_id=message.from_user.id)
            .order_by(desc(Place.created_at))
            .limit(10)
            .all()
        )

        if places:
            keyboard = get_show_places_keyboard(places)
            await message.answer(
                'Выберите одно из представленных мест', reply_markup=keyboard
            )
            await state.set_state('LIST_RECENT')
        else:
            await state.reset_state(with_data=False)
            await message.answer(
                'У вас нет сохраненных мест'
            )
            await message.answer(
                'Выберите действие', reply_markup=start_keyboard
            )


@dp.callback_query_handler(MenuCB.filter(action='list'))
async def cq_list(query: types.CallbackQuery, state: FSMContext):
    nearest_button = types.InlineKeyboardButton(
        'Места в радиусе 500 метров',
        callback_data=ListModeCB.new(mode='nearest'),
    )
    recent_button = types.InlineKeyboardButton(
        'Последние 10 добавленных мест',
        callback_data=ListModeCB.new(mode='recent'),
    )
    buttons = [
        [nearest_button],
        [recent_button],
        [back_button],
    ]
    keyboard = types.InlineKeyboardMarkup(row_width=1, inline_keyboard=buttons)
    await query.message.edit_text('Какие места вы хотите увидеть?')
    await query.message.edit_reply_markup(keyboard)
    await state.set_state('CHOOSE_LIST_MODE')
    await query.answer()


@dp.callback_query_handler(MenuCB.filter(action='back'),
                           state='CHOOSE_LIST_MODE')
async def cq_back_to_main_menu(query: types.CallbackQuery, state: FSMContext):
    await state.reset_state(with_data=False)
    await query.message.edit_text(
        'Выберите действие', reply_markup=start_keyboard
    )
    await query.answer()


@dp.callback_query_handler(MenuCB.filter(action='back'),
                           state='CHOOSE_PLACE')
async def cq_back_to_list_mode(
    query: types.CallbackQuery, state: FSMContext
):
    await cq_list(query, state)


@dp.callback_query_handler(ListModeCB.filter(mode='nearest'),
                           state='CHOOSE_LIST_MODE')
async def cq_nearest_places(query: types.CallbackQuery, state: FSMContext):
    await state.set_state('LIST_NEAREST')
    await query.message.answer('Отправьте свою геолокацию')
    await query.answer()


@dp.message_handler(content_types=types.ContentType.LOCATION,
                    state='LIST_NEAREST')
async def nearest_places(message: types.Message, state: FSMContext):
    _ = User(telegram_user_id=message.from_user.id).from_db()

    dest_places = (
        session
        .query(Place)
        .select_from(User)
        .join(User.places)
        .filter(User.telegram_user_id == message.from_user.id)
        .all()
    )

    location = message.location
    user_location = {
        'latitude': location.latitude,
        'longitude': location.longitude,
        'created_at': datetime.utcnow().isoformat(),
    }
    await state.update_data(user_location=user_location)

    dist_to_places = await distances_from_location_to_places(
        message.location, dest_places
    )
    places = [
        place for place, dist in dist_to_places.items() if dist <= 500
    ]

    if places:
        keyboard = get_show_places_keyboard(places)
        await state.set_state('CHOOSE_PLACE')
        await message.answer(
            'Выберите одно из представленных мест', reply_markup=keyboard
        )
    else:
        await message.answer('Ближайших мест в радиусе 500 метров не найдено')
        await state.reset_state(with_data=False)
        await message.answer('Выберите действие', reply_markup=start_keyboard)


@dp.callback_query_handler(ListModeCB.filter(mode='recent'),
                           state='CHOOSE_LIST_MODE')
async def cq_recent_places(query: types.CallbackQuery, state: FSMContext):
    places = (
        session
        .query(Place)
        .select_from(User)
        .join(User.places)
        .filter(User.telegram_user_id == query.from_user.id)
        .order_by(desc(Place.created_at))
        .limit(10)
        .all()
    )

    if places:
        keyboard = get_show_places_keyboard(places)
        await query.message.edit_text(
            'Выберите одно из представленных мест',
            reply_markup=keyboard,
        )
        await state.set_state('CHOOSE_PLACE')
    else:
        await state.reset_state(with_data=False)
        await query.message.answer('У вас нет сохраненных мест')
        await query.message.answer(
            'Выберите действие', reply_markup=start_keyboard
        )

    await query.answer()


@dp.callback_query_handler(PlaceCB.filter(), state='CHOOSE_PLACE')
async def cq_show_place(
    query: types.CallbackQuery, state: FSMContext, callback_data: dict
):
    place = session.get(Place, int(callback_data['id']))
    photos = [photo.telegram_file_id for photo in place.photos]

    await query.message.answer_venue(
        place.latitude, place.longitude, place.title, place.address
    )
    await show_place_photos(query.message, photos)
    await state.reset_state(with_data=False)
    await query.message.answer(
        'Выберите действие', reply_markup=start_keyboard
    )
    await query.answer()
