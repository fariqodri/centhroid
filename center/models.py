from django.db import models
from typing import Tuple
import requests, re
import googlemaps
from centhroid.settings import MAPS_GEOCODE_API_KEY
from urllib.parse import urlparse

URL_FORMAT = 'https://www.google.com/maps/place/?q=place_id:%s'

# Create your models here.
class Location:
    def __init__(self, url: str, plus_code: str, coordinate: Tuple[float, float], address: str):
        self.url = url
        self.plus_code = plus_code
        self.coordinate = coordinate
        self.address = address

    @staticmethod
    def from_url(url: str):
        if MapPin.is_short_url(url):
            return Location.from_short_url(url)
    
        return Location.from_long_url(url)

    @staticmethod
    def from_short_url(short_url: str):
        response = requests.get(short_url)
        if response.status_code >= 400:
            return None
        
        long_url = response.url
        return Location.from_long_url(long_url)

    @staticmethod
    def from_address(address: str):
        gmaps = googlemaps.Client(key=MAPS_GEOCODE_API_KEY)
        geocode = gmaps.geocode(address)
        if len(geocode) == 0:
            return None
        
        maps_location: dict = geocode[0]
        url = URL_FORMAT % (maps_location['place_id'])
        plus_code = maps_location.get('plus_code', {}).get('global_code', None)
        coordinate = tuple(maps_location.get('geometry', {}).get('location', {}).values())
        return Location(
            url=url,
            plus_code=plus_code,
            coordinate=coordinate,
            address=maps_location.get('formatted_address')
        )
    
    @staticmethod
    def from_long_url(long_url: str):
        regex_coordinate = r"!\dd([-?\d\.]*)"
        gmaps = googlemaps.Client(key=MAPS_GEOCODE_API_KEY)
        coordinate_component = re.findall(regex_coordinate, long_url)
        coordinate = ",".join(coordinate_component)
        geocode = gmaps.geocode(coordinate)
        if len(geocode) == 0:
            return None
        
        maps_location: dict = geocode[0]
        url = URL_FORMAT % (maps_location['place_id'])
        plus_code = maps_location.get('plus_code', {}).get('global_code', None)
        return Location(
            url=url,
            plus_code=plus_code,
            coordinate=coordinate,
            address=maps_location.get('formatted_address')
        )
    
    def __str__(self) -> str:
        return str(vars(self))
    
class MapPin:
    def __init__(self, coordinate: Tuple[float, float], title: str = None):
        self.coordinate = coordinate
        self.title = title

    def encode_to_marker(self) -> str:
        marker = ','.join(map(str, self.coordinate))
        if self.title:
            marker += '|title=%s' % (self.title)
        return marker

    @staticmethod
    def is_url(pin: str) -> bool:
        parsed = urlparse(pin)
        if parsed.scheme and parsed.netloc:
            return True
        
        return False
    
    @staticmethod
    def is_long_url(url: str) -> bool:
        return 'google.com/maps' in url

    @staticmethod
    def is_short_url(url: str) -> bool:
        return 'goo.gl/maps' in url

class Establishment:
    def __init__(self, title: str, id: str):
        self.title = title
        self.id = id
    
    def __str__(self) -> str:
        return 'Establishment(title="%s", id="%s")' % (self.title, self.id)

class NearbyPlace:
    def __init__(self, name: str, coordinate: Tuple[float, float], icon: str, establishment_type: Establishment, url: str, rating: float, address: str, num_of_ratings: int) -> None:
        self.name = name
        self.coordinate = coordinate
        self.icon = icon
        self.url = url
        self.rating = rating
        self.address = address
        self.num_of_ratings = num_of_ratings
        self.establishment_type = establishment_type
    
    def __str__(self) -> str:
        return '{}, {}'.format(self.name, self.url)