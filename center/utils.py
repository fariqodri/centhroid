from math import radians, cos, sin, sqrt, atan2, degrees
from centhroid.settings import MAPS_EMBED_API_KEY, MAPS_NEARBY_API_KEY
from typing import Tuple, List
import numpy as np
import logging
import googlemaps
from .models import MapPin, NearbyPlace, URL_FORMAT, Establishment
from .establishments import ESTABLISHMENTS

logger = logging.getLogger(__name__)

def center_lat_long(coordinates: List[Tuple[float, float]]):
    x = 0
    y = 0
    z = 0
    for lat, lon in coordinates:
        lat = radians(lat)
        lon = radians(lon)
        x += cos(lat) * cos(lon)
        y += cos(lat) * sin(lon)
        z += sin(lat)
        
    x /= len(coordinates)
    y /= len(coordinates)
    z /= len(coordinates)
    center_lon = atan2(y, x)
    hyp = sqrt(x * x + y * y)
    center_lat = atan2(z, hyp)
    center_lat = degrees(center_lat)
    center_lon = degrees(center_lon)
    return center_lat, center_lon

def fermat_weber(points):
    """
    Calculates the Fermat-Weber point given a set of points in 2D or 3D space.

    Args:
        points (numpy array): A numpy array of shape (n, d) representing n points in d-dimensional space.

    Returns:
        A numpy array of shape (d,) representing the coordinates of the Fermat-Weber point.
    """

    # Number of points
    points = np.asarray(points)
    n = points.shape[0]

    # Initialize point positions as the mean of all the points
    p = np.mean(points, axis=0)

    # Calculate the distance from the initial point to all other points
    dist = np.linalg.norm(points - p, axis=1)

    i = 0
    ITERATION_LIMIT = 10000
    # Iterate until convergence
    while True:

        # Calculate the weight for each point based on its distance to the current point
        w = dist / np.sum(dist)

        # Calculate the weighted average of all points
        p_new = np.average(points, axis=0, weights=w)

        # Calculate the distance from the new point to all other points
        dist_new = np.linalg.norm(points - p_new, axis=1)

        # Check for convergence or iteration has reached limit
        if np.allclose(dist, dist_new) or i > ITERATION_LIMIT:
            logger.info('Fermat-Weber Point converges after %d iterations', i)
            return p_new
        else:
            p = p_new
            dist = dist_new
        
        i += 1

def embed_url_generator(input_map_pins: List[MapPin], center_map_pin: MapPin) -> str:
    url = 'https://www.google.com/maps/embed/v1/view?key={api_key}&center={center_coordinate}&zoom=12&markers={markers}'
    center_coordinate = ','.join(map(str, center_map_pin.coordinate))
    markers: List[str] = []
    for p in input_map_pins:
        markers.append(p.encode_to_marker())
    markers.append(center_map_pin.encode_to_marker())
    return url.format_map({'api_key': MAPS_EMBED_API_KEY, 'center_coordinate': center_coordinate, 'markers': '&'.join(markers)})

def generate_place_url(place_id: str):
    return URL_FORMAT % (place_id)

def get_nearby_attractions(coordinate: Tuple[float, float], establishment_types: List[Establishment], radius = 100, max_results = 20, results_per_type = 5) -> List[NearbyPlace]:
    if len(establishment_types) == 0:
        return []
    
    results: List[NearbyPlace] = []
    gmaps = googlemaps.Client(key=MAPS_NEARBY_API_KEY)
    for type in establishment_types:
        response: dict = gmaps.places_nearby(location=coordinate, radius=radius, type=type.id, rank_by='prominence')
        if response.get('status', 'unknown') != 'OK':
            logger.warn('Fetching places nearby failed for coordinate %s and type %s because of %s', coordinate, type.id, response.get('error_message', 'unknown'))
            continue
        
        places: List[dict] = response.get('results', [])
        if len(places) == 0:
            continue
        
        for place in places[:results_per_type]:
            place_name = place.get('name')
            lat = place.get('geometry', {}).get('location', {}).get('lat')
            long = place.get('geometry', {}).get('location', {}).get('lng')
            icon = place.get('icon')
            place_id = place.get('place_id')
            rating = place.get('rating', 0)
            address = place.get('vicinity')
            num_of_ratings = place.get('user_ratings_total', 0)
            nearby_place = NearbyPlace(
                name=place_name,
                coordinate=(lat, long),
                icon=icon,
                url=generate_place_url(place_id),
                rating=rating,
                address=address,
                num_of_ratings=num_of_ratings,
                establishment_type=type
            )
            results.append(nearby_place)

    results = sorted(results, key=lambda p: p.rating * p.num_of_ratings, reverse=True)
    return results[:max_results]

def get_establishment_by_id(id: str) -> Establishment:
    for establishment in ESTABLISHMENTS:
        if establishment.id == id:
            return establishment
    
    return None