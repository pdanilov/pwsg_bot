from typing import List

from app.models import Photo, Place, User, session


def store_user_place_photos(user: User, place: Place, photos: List[Photo]):
    user = user.from_db()
    place = place.from_db()

    if place not in user.places:
        user.places.append(place)

    for photo in photos:
        photo = photo.from_db(place)
        photo.place = place

        if photo.place_id is None:
            place.photos.append(photo)

    session.commit()
