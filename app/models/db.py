import sqlalchemy as sa
from aiogram import Dispatcher
from aiogram.utils.executor import Executor
from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

from app import config

Base = declarative_base()
engine = create_engine(config.POSTGRESQL_URI, client_encoding='utf8')
session = Session(engine)


class ReprBaseModel(Base):
    __abstract__ = True

    def columns(self) -> dict:
        try:
            columns = self.__table__.columns.keys()
            kwargs = {
                column: getattr(self, column)
                for column in columns
            }
        except AttributeError:
            kwargs = {}

        return kwargs

    def __repr__(self):
        class_repr = self.__class__.__name__
        columns = self.columns()
        columns_repr = ', '.join(
            f'{k}={repr(v)}'
            for k, v in columns.items()
        )
        return f'{class_repr}({columns_repr})'


class TimedBaseModel(ReprBaseModel):
    __abstract__ = True

    created_at = sa.Column(
        sa.DateTime(timezone=True),
        default=sa.func.now(),
    )
    updated_at = sa.Column(
        sa.DateTime(timezone=True),
        onupdate=sa.func.now(),
        default=sa.func.now(),
    )


async def on_startup(_: Dispatcher):
    logger.info('Setup PostgreSQL')
    Base.metadata.create_all(engine)


async def on_shutdown(_: Dispatcher):
    logger.info('Close PostgreSQL connection')
    session.close()


def setup(executor: Executor):
    executor.on_startup(on_startup)
    executor.on_shutdown(on_shutdown)
