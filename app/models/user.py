import sqlalchemy as sa
from sqlalchemy.orm import Session

from app.models.db import TimedBaseModel


class User(TimedBaseModel):
    __tablename__ = 'user'

    id = sa.Column(sa.Integer, primary_key=True)
    telegram_user_id = sa.Column(sa.BigInteger)

    def from_db(self, session: Session) -> 'User':
        user = (
           session
           .query(User)
           .filter_by(telegram_user_id=self.telegram_user_id)
           .one_or_none()
        )
        if user:
            return user

        session.add(self)
        session.flush()
        return self
