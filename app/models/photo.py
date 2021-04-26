import sqlalchemy as sa
from sqlalchemy.orm import Session

from app.models.db import TimedBaseModel
from app.models.place import Place


class Photo(TimedBaseModel):
    __tablename__ = 'photo'

    place_id = sa.Column(sa.Integer, sa.ForeignKey('place.id'))
    telegram_file_id = sa.Column(sa.String, primary_key=True)
    telegram_file_unique_id = sa.Column(sa.String)

    def from_db(self, place: Place, session: Session) -> 'Photo':
        photo = (
            session
            .query(Photo)
            .filter(sa.and_(
                Photo.telegram_file_unique_id == self.telegram_file_unique_id,
                place.id == self.place_id,
            ))
            .one_or_none()
        )
        if photo:
            return photo

        session.add(self)
        session.flush()
        return self
