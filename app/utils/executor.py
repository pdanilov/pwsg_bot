from aiogram.utils.executor import Executor
from loguru import logger

from app.misc import dp
from app.models import db
from app.utils import dispatcher

executor = Executor(dp)


def setup():
    logger.info("Configure executor")
    db.setup(executor)
    dispatcher.setup(executor)
