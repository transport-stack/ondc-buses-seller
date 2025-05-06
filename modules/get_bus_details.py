import logging
import os
from django.core.cache import cache

import requests


def fetch_vehicle_data(vehicle_id):
    fleet_data_cache_key = "fleet_data"
    vehicle_list = cache.get(fleet_data_cache_key)
    if vehicle_list is None:
        fleet_data = requests.get(os.getenv('FLEET_DATA_URL'))
        vehicle_list = fleet_data.json()
        # logging.info(f"Vehicle list======: {vehicle_list}")
        cache.set(fleet_data_cache_key, fleet_data.json(), timeout=60 * 60 * 24)
    for vehicle in vehicle_list:
        if vehicle['vehicle_id'] == vehicle_id:
            return vehicle
    return None
