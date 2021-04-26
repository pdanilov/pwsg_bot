from app import misc
from app.misc import dp
from app.utils.executor import executor


if __name__ == '__main__':
    misc.setup()
    executor.start_polling(dp)
