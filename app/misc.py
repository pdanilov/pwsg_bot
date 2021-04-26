from urllib.parse import urlparse

from aiogmaps import Client as AsyncClient
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.redis import RedisStorage2
from googlemaps import Client

from app import config

bot = Bot(token=config.BOT_TOKEN, parse_mode=types.ParseMode.HTML)
redis_url = urlparse(config.REDIS_URL)
storage = RedisStorage2(
    host=redis_url.hostname, port=redis_url.port, password=redis_url.password
)
dp = Dispatcher(bot, storage=storage)
gmaps_client = Client(key=config.GOOGLE_MAPS_API_KEY)
gmaps_async_client = AsyncClient(key=config.GOOGLE_MAPS_API_KEY)


def setup():
    from app import handlers
    from app.utils import executor, logging
    executor.setup()
    logging.setup()
    handlers.setup()
