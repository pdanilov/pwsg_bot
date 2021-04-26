from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.utils.markdown import hitalic, hbold
from loguru import logger

from app.misc import dp
from app.utils.keyboards import start_keyboard


@dp.message_handler(commands=['start'], state='*')
async def cmd_start(message: types.Message, state: FSMContext):
    await state.finish()
    text = (
        f'Привет, {message.from_user.full_name}\n'
        'Можешь отправить команду /help, чтобы узнать список доступных команд '
        'или воспользоваться клавиатурой'
    )
    await message.answer(text)
    await cmd_main_menu(message, state)


@dp.message_handler(commands=['help'], state='*')
async def cmd_help(message: types.Message, state: FSMContext):
    await state.finish()
    text = '\n'.join((
        hbold('Доступные команды:'),
        '',
        '/add - добавить место',
        '/add ' + hitalic('название/адрес') + ' - добавить место по запросу',
        '/list - показать список мест в радиусе 500 метров',
        '/list recent - показать список 10 последних добавленных мест',
        '/reset - очистить записную книгу',
        '/help - отобразить список доступных команд',
        '/menu - показать главное меню',
        '/cancel - прекратить диалог, вернуться в главное меню',
    ))
    await message.answer(text)


@dp.message_handler(commands=['cancel', 'menu'], state='*')
async def cmd_main_menu(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer('Выберите действие', reply_markup=start_keyboard)


@dp.errors_handler()
async def errors_handler(update: types.Update, exception: Exception):
    try:
        raise exception
    except Exception as e:
        logger.exception(f'Cause exception {e} in update {update}')
    return True
