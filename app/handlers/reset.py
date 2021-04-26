from aiogram import types
from aiogram.dispatcher import FSMContext

from app.misc import dp
from app.models import session, User, Place
from app.utils.keyboards import (
    ConfirmCB, MenuCB, confirm_cancel_keyboard, start_keyboard,
)


@dp.message_handler(commands=['reset'], state='*')
async def cmd_reset(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer(
        'Вы действительно хотите удалить все сохраненные места?',
        reply_markup=confirm_cancel_keyboard,
    )


@dp.callback_query_handler(MenuCB.filter(action='reset'))
async def cq_reset(query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await query.message.edit_text(
        'Вы действительно хотите удалить все сохраненные места?',
        reply_markup=confirm_cancel_keyboard,
    )
    await query.answer()


@dp.callback_query_handler(ConfirmCB.filter(answer='yes'))
async def cq_confirm_reset(query: types.CallbackQuery):
    user = (
        session
        .query(User)
        .filter_by(telegram_user_id=query.from_user.id)
        .one_or_none()
    )

    if user:
        places_to_delete = (
            session
            .query(Place)
            .select_from(User)
            .join(User.places)
            .filter(Place.id.notin_([place.id for place in user.places]))
            .all()
        )

        for place in places_to_delete:
            session.delete(place)

        session.delete(user)
        session.commit()

    await query.message.edit_text(
        'Выберите действие', reply_markup=start_keyboard
    )
    await query.answer()


@dp.callback_query_handler(ConfirmCB.filter(answer='no'))
async def cq_cancel_reset(query: types.CallbackQuery):
    await query.message.edit_text(
        'Выберите действие', reply_markup=start_keyboard
    )
    await query.answer()
