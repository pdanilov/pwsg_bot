from aiogram import Dispatcher
from aiogram.utils.executor import Executor


async def on_startup(_: Dispatcher):
    pass


async def on_shutdown(dispatcher: Dispatcher):
    await dispatcher.bot.session.close()
    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()


def setup(executor: Executor):
    executor.on_startup(on_startup)
    executor.on_shutdown(on_shutdown)
