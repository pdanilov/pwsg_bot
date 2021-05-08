import sqlalchemy as sa
from sqlalchemy.orm import relationship

from app.models.db import TimedBaseModel, session
from app.models.relationship import user_to_place


class Place(TimedBaseModel):
    __tablename__ = 'place'

    id = sa.Column(sa.Integer, primary_key=True)
    title = sa.Column(sa.Text)
    address = sa.Column(sa.Text)
    latitude = sa.Column(sa.Float(precision=6))
    longitude = sa.Column(sa.Float(precision=6))
    gmaps_place_id = sa.Column(sa.String, nullable=True)

    users = relationship(
        'User', secondary=user_to_place, backref='places'
    )
    photos = relationship(
        'Photo', cascade='all, delete-orphan', backref='place'
    )

    def from_db(self) -> 'Place':
        place = (
            session
            .query(Place)
            .filter(sa.and_(
                self.gmaps_place_id is not None,
                Place.gmaps_place_id == self.gmaps_place_id,
            ))
            .one_or_none()
        )
        if place:
            return place

        session.add(self)
        session.flush()
        return self
