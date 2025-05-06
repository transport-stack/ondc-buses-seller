import cProfile
import io
import json
import logging
import os
import pstats
from datetime import timezone, datetime, time
import requests
from celery import shared_task
from django.core.cache import cache
from main.tasks.task_send_no import task_push_txn_logs
from main.constants import CACHE_TIMEOUT, CACHE_DELIMITER, TIMESTAMP_CACHE_TIMEOUT, MAX_PAX_COUNT, MIN_PAX_COUNT, DIMTS_FULL, DTC_FULL
from main.transformers import SearchTransformer
from main.utils.post_request import post_request
from main.utils.time_parser import get_current_utc_timestamp
from modules.fare_setup.main import FareCalculator
from main.constants import payments_array


def profile_task(func):
    def wrapper(*args, **kwargs):
        profiler = cProfile.Profile()
        profiler.enable()
        result = func(*args, **kwargs)
        profiler.disable()
        s = io.StringIO()
        sortby = 'cumulative'
        ps = pstats.Stats(profiler, stream=s).sort_stats(sortby)
        ps.print_stats()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'profiles/{func.__name__}_celery_profiling_stats_{timestamp}.prof'
        profiler.dump_stats(filename)

        # with open(f'profiles/{func.__name__}_celery_profiling_stats_{timestamp}.txt', 'a') as f:
        #     f.write(s.getvalue())
        return result

    return wrapper


@shared_task(name="main.tasks.on_search")
def on_search(on_search_request):
    try:
        routes_data, sequence_dict = SearchTransformer().ondc_to_chartr_v2(on_search_request)
        if not routes_data or not sequence_dict:
            logging.error(f"No routes or sequence found for the search request. {on_search_request}")
            return {f'No routes or sequence found for the search request. {on_search_request}'}

        context_data = on_search_request.get('context')
        vehicle_data = on_search_request.get('vehicle')
        registration = vehicle_data.get('registration', None)
        bap_uri = context_data['bap_uri']
        bap_uri += 'on_search' if bap_uri.endswith('/') else '/on_search'

        formatted_current_utc = get_current_utc_timestamp()
        context_data['timestamp'] = formatted_current_utc
        transaction_id = context_data['transaction_id']
        logging.fatal(f"on_search received at seller,{transaction_id},{datetime.now(timezone.utc)}")
        context_data['bpp_id'] = os.environ.get('BPP_ID')
        context_data['bpp_uri'] = os.environ.get('BPP_URL')
        context_data['action'] = "on_search"

        start_stop = next(filter(lambda x: x.get('type') == 'START', on_search_request.get('stops', [])), None)
        end_stop = next(filter(lambda x: x.get('type') == 'END', on_search_request.get('stops', [])), None)
        start_code = start_stop['location']['descriptor']['code'] if start_stop else 'START_CODE_UNKNOWN'
        end_code = end_stop['location']['descriptor']['code'] if end_stop else 'END_CODE_UNKNOWN'

        provider_map = {}
        item_counter = 1
        fulfillment_counter = 1

        # if len(routes_data) > 1:
        #     routes = tuple([x['route_id'] for x in routes_data])
        # else:
        #     routes = (routes_data)

        routes = ','.join(map(str, [x['route_id'] for x in routes_data]))

        calculator = FareCalculator()
        intermediate_stops_dict = (calculator.fetch_intermediate_stops_with_gps(routes=routes, start_stop_code=start_code, end_stop_code=end_code,
                                                                                sequence_dict=sequence_dict))

        if not routes_data:
            logging.error("No routes found.")

        current_date = datetime.now(timezone.utc).date()
        operational_start_time = datetime.combine(current_date, time(hour=6, minute=0)).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        operational_end_time = datetime.combine(current_date, time(hour=23, minute=0)).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

        for route in routes_data:
            agency = route.get('agency')
            if agency not in provider_map:
                provider_map[agency] = {
                    "id": f"P{len(provider_map) + 1}",
                    "name": DTC_FULL if agency == "DTC" else DIMTS_FULL if agency == "DIMTS" else "Unknown Agency",
                    "items": [],
                    "fulfillments": []
                }

            route_id = str(route['route_id'])
            route_name = route.get('route_name', 'Unknown Route')
            fare = route.get('fare', 'N/A')
            start_stop_name = route.get('start_stop_name')
            end_stop_name = route.get('end_stop_name')
            direction = route.get('direction', 'N/A')
            air_conditioned = route.get('air_conditioned', False)
            start_stop_gps = route.get('start_stop_gps', 'N/A')
            end_stop_gps = route.get('end_stop_gps', 'N/A')
            formatted_start_gps = f"{start_stop_gps}, {start_stop_gps}" if (start_stop_gps != 'N/A') else 'N/A'
            formatted_end_gps = f"{end_stop_gps}, {end_stop_gps}" if (end_stop_gps != 'N/A') else 'N/A'

            item_id = f"I{item_counter}"
            fulfillment_id = f"F{fulfillment_counter}"

            item = {
                "id": item_id,
                "descriptor": {
                    "name": f"{route_name}",
                    "code": "SJT",
                    "images": [{"url": "https://transitsolutions.in/logos/logo.icon", "size_type": "xs"}]
                },
                "fulfillment_ids": [fulfillment_id],
                "price": {"currency": "INR", "value": str(fare)},
                "quantity": {"maximum": {"count": MAX_PAX_COUNT}, "minimum": {"count": MIN_PAX_COUNT}},
                "time": {"label": "Validity", "duration": "PT1D"}
            }

            intermediate_stops = intermediate_stops_dict[route_id]
            length_of_intermediate_stops = len(intermediate_stops)
            fulfillment = {
                "id": fulfillment_id,
                "type": "TRIP",
                "stops": [
                    {"type": "START", "location": {"descriptor": {"name": start_stop_name, "code": start_code}, "gps": formatted_start_gps},
                     "id": "1"},
                    *intermediate_stops,
                    {"type": "END", "location": {"descriptor": {"name": end_stop_name, "code": end_code}, "gps": formatted_end_gps},
                     "id": f"{length_of_intermediate_stops + 2}", "parent_stop_id": f"{length_of_intermediate_stops + 1}"}
                ],
                "vehicle": {"category": "BUS", "variant": "AC" if air_conditioned else "NAC", "registration": registration},
                "tags": [
                    {"descriptor": {"code": "ROUTE_INFO"}, "list": [
                        {"descriptor": {"code": "ROUTE_ID"}, "value": str(route_id)},
                        {"descriptor": {"code": "ROUTE_DIRECTION"}, "value": direction},
                        {"descriptor": {"code": "OPERATIONAL_START_TIME"}, "value": f"{operational_start_time}"},
                        {"descriptor": {"code": "OPERATIONAL_END_TIME"}, "value": f"{operational_end_time}"}
                    ]}
                ]
            }

            provider_map[agency]['items'].append(item)
            provider_map[agency]['fulfillments'].append(fulfillment)

            item_counter += 2
            fulfillment_counter += 1

        providers = [{
            "id": provider_data['id'],
            "descriptor": {
                "name": provider_data['name'],
                "images": [{"url": "https://dtc.delhi.gov.in/sites/default/files/DTC/logo/dtc_logo_2.png", "size_type": "xs"}]
            },
            "items": provider_data['items'],
            "fulfillments": provider_data['fulfillments'],
            "payments": payments_array
        } for provider_data in provider_map.values()]

        formatted_json_response = {
            "context": context_data,
            "message": {
                "catalog": {
                    "descriptor": {"name": "Transport Dept.", "images": [{"url": "https://transitsolutions.in/logos/logo.ico", "size_type": "xs"}]},
                    "providers": providers
                }
            }
        }

        cache_key = f"{transaction_id}:search"
        cache.set(cache_key, formatted_json_response, timeout=CACHE_TIMEOUT)

        if bap_uri:

            on_search_start_time_cache_key = f"{transaction_id}:{CACHE_DELIMITER}:on_search_start_time"
            # logging.info(f"search_start_time_cache_key=======: {on_search_start_time_cache_key}")

            cache.set(on_search_start_time_cache_key, formatted_current_utc, timeout=TIMESTAMP_CACHE_TIMEOUT)
            search_timestamp_data = cache.get(on_search_start_time_cache_key)
            # logging.info(f"search_timestamp_data==========: {search_timestamp_data}")

            status_code, post_result = post_request(bap_uri, formatted_json_response)

            logging.info(f"SEARCH Response from BAP=====status_code:=={status_code}==txn_id:==={transaction_id}:===response:==== {post_result}")
            action = context_data['action']
            task_push_txn_logs.apply_async(args=[action, formatted_json_response])

            return {"success": True}
        else:
            logging.error("BAP URI not found.")

    except Exception as e:
        logging.error(f"Unexpected error for the request {on_search_request}: {str(e)}")
        return {'error': f"Unexpected error in on_search {on_search_request}: {str(e)}"}

