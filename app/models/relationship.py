import sqlalchemy as sa

from app.models.db import Base

user_to_place = sa.Table(
    "user_to_place",
    Base.metadata,
    sa.Column("user_id", sa.Integer, sa.ForeignKey("user.id")),
    sa.Column("place_id", sa.Integer, sa.ForeignKey("place.id")),
)
