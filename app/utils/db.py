from typing import List

from app.models import session, Photo, Place, User


def store_user_place_photos(
    user: User,
    place: Place,
    photos: List[Photo],
):
    user = user.from_db(session)
    place = place.from_db(session)

    if place not in user.places:
        user.places.append(place)

    for photo in photos:
        photo = photo.from_db(place, session)
        photo.place = place

        if photo.place_id is None:
            place.photos.append(photo)

    session.commit()
