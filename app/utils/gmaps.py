import io
from tempfile import TemporaryFile
from typing import Dict, List, Optional

from aiogram import types

from app.misc import gmaps_async_client, gmaps_client
from app.models import Place


def place_info_from_query(query: str) -> Optional[Dict]:
    response = gmaps_client.places(query=query, language='ru')

    if response['status'] != 'OK':
        return

    result = response['results'][0]
    result_dict = {
        'title': result['name'],
        'address': result['formatted_address'],
        'latitude': result['geometry']['location']['lat'],
        'longitude': result['geometry']['location']['lng'],
        'gmaps_place_id': result['place_id'],
        'photo_references': [
            item['photo_reference']
            for item in result.get('photos', [])
        ],
    }
    return result_dict


async def distances_from_location_to_places(
    src_location: types.Location, dst_places: List[Place]
) -> Dict[Place, float]:
    origin = (src_location.latitude, src_location.longitude)
    destinations = [
        (place.latitude, place.longitude)
        for place in dst_places
    ]

    if not destinations:
        return {}

    response = await gmaps_async_client.distance_matrix(
        origin, destinations, mode='walking', language='ru'
    )

    if response['status'] == 'OK':
        distances = [
            item['distance']['value']
            for item in response['rows'][0]['elements']
        ]
    else:
        distances = []

    place_to_distance = {
        place: distance
        for place, distance in zip(dst_places, distances)
    }
    return place_to_distance


async def gmaps_input_photo(photo_ref: str) -> types.InputFile:
    with TemporaryFile() as input_file:
        async for chunk, _ in await gmaps_async_client.places_photo(
            photo_ref, max_width=1920
        ):
            if chunk:
                input_file.write(chunk)

        input_file.seek(0)
        bytes_io = io.BytesIO(input_file.read())
        input_file = types.InputFile(bytes_io)

    return input_file
