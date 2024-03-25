from django.shortcuts import render, redirect, resolve_url
from django.http import HttpRequest
from typing import List, Tuple
from .models import Location, MapPin
from . import utils
from centhroid.settings import MAPS_EMBED_API_KEY, MAPS_ID, MAPS_AUTOCOMPLETE_API_KEY
from django.contrib import messages
from .establishments import ESTABLISHMENTS
from django_user_agents.utils import get_user_agent

# Create your views here.
def index(request: HttpRequest):
    input_keywords = request.GET.getlist('keyword')
    input_establishments = request.GET.getlist('establishment')
    input_keywords = [pin for pin in input_keywords if len(pin) > 0]
    location_labels = [chr(65 + i) for i in range(len(input_keywords))]
    context = {
        'locations': list(zip(location_labels, input_keywords)), 
        'establishment_options': ESTABLISHMENTS,
        'selected_establishments': input_establishments,
        'autoselected_establishments': ['restaurant', 'cafe'],
        'embed_api_key': MAPS_AUTOCOMPLETE_API_KEY
    }
    return render(request, 'form.html', context=context)

def find_center(request: HttpRequest):
    input_keywords = request.GET.getlist('keyword')
    input_establishments = request.GET.getlist('establishment')
    raw_query = request.META.get('QUERY_STRING')
    user_agent = get_user_agent(request)
    print(user_agent)
    if len(input_keywords) > 20:
        messages.error(request, 'Number of input locations exceeds limit (20 locations)')
        return redirect(resolve_url('index') + '?%s' % (raw_query))
    
    locations: List[Tuple[str, Location]] = []
    for i in range(0, len(input_keywords)):
        input_keyword = input_keywords[i].strip()
        label = chr(65 + i)
        if len(input_keyword) == 0:
            messages.error(request, 'Location %s is empty' % (label))
            return redirect(resolve_url('index') + '?%s' % (raw_query))
        if MapPin.is_url(input_keyword):
            location = Location.from_url(input_keyword)
        else:
            location = Location.from_address(input_keyword)

        if location == None:
            messages.error(request, 'Location %s (%s) not found on Google Maps. Please insert more detailed keywords' % (label, input_keyword))
            return redirect(resolve_url('index') + '?%s' % (raw_query))
        locations.append((label, location))

    coordinates = [location.coordinate for _, location in locations]
    if len(coordinates) < 2:
        messages.error(request, 'Invalid location keywords')
        return redirect(resolve_url('index') + '?%s' % (raw_query))

    center_lat, center_long = utils.fermat_weber(coordinates)
    center_coordinate = '{},{}'.format(center_lat, center_long)
    center_location = Location.from_address(center_coordinate)

    number_of_places = 20
    if user_agent.is_mobile:
        number_of_places = 15

    input_establishments = [utils.get_establishment_by_id(establishment_id) for establishment_id in input_establishments]
    nearby_places = utils.get_nearby_attractions(
        coordinate=(center_lat, center_long),
        establishment_types=input_establishments,
        radius=1000,
        max_results=number_of_places
    )
    context = {
        'locations': locations, 
        'center': center_location, 
        'embed_api_key': MAPS_EMBED_API_KEY, 
        'input_locations': input_keywords,
        'input_establishments': input_establishments,
        'nearby_places': nearby_places,
        'map_id': MAPS_ID
    }
    return render(request, 'result.html', context=context)

def feature_page(request: HttpRequest):
    return render(request, 'features.html')