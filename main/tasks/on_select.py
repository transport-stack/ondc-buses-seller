import cProfile
import io
import logging
import pstats
from datetime import timezone, datetime
import requests
from celery import shared_task
from django.core.cache import cache
from main.constants import CACHE_TIMEOUT, DISCOUNT, CACHE_DELIMITER, \
    TIMESTAMP_CACHE_TIMEOUT, PINK_TICKET_FARE
from main.tasks.task_send_no import task_push_txn_logs
from main.utils.post_request import post_request
from main.utils.time_parser import get_current_utc_timestamp
from modules.fare_setup.main import FareCalculator


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


@shared_task(name="main.tasks.on_select")
# @profile_task
def on_select(on_select_request):
    try:
        context_data = on_select_request.get('context')
        context_data['action'] = "on_select"

        formatted_current_utc = get_current_utc_timestamp()
        context_data['timestamp'] = formatted_current_utc

        selected_item = on_select_request.get('item')
        selected_provider = on_select_request.get('provider')
        transaction_id = context_data['transaction_id']
        logging.fatal(f"on_select received at seller,{transaction_id},{datetime.now(timezone.utc)}")
        bap_url_base = context_data['bap_uri']
        bap_uri = f'{bap_url_base}/on_select'
        logging.info("bap_uri============%s", bap_uri)  # For debugging
        stored_data = cache.get(f'{transaction_id}:search')
        logging.info("Stored search data============%s", stored_data is not None)  # For debugging
        if not stored_data:
            logging.error(f"No data found for the given transaction ID : {transaction_id}")
            raise Exception("No data found for the given transaction ID")

        for provider in stored_data['message']['catalog']['providers']:
            for fulfillment in provider.get('fulfillments', []):
                for tag in fulfillment['tags']:
                    tag['list'] = [
                        entry for entry in tag['list']
                        if entry['descriptor']['code'] not in (
                            "OPERATIONAL_START_TIME", "OPERATIONAL_END_TIME")
                    ]
        # Get item and provider IDs from the on_select_request
        request_item_id = selected_item[0]['id']
        request_provider_id = selected_provider['id']
        request_secected_count = selected_item[0]['quantity']['selected']['count']

        # Find the selected item and provider in the stored data
        selected_item = None
        selected_provider = None
        for provider in stored_data['message']['catalog']['providers']:
            if provider['id'] == request_provider_id:
                selected_provider = provider
                for item in provider['items']:
                    if item['id'] == request_item_id:
                        selected_item = item
                        break
                break
        ticket_category = selected_item['descriptor']['code']
        if not selected_item or not selected_provider:
            logging.error("Selected item or provider not found in the stored data")

        # Build the provider_map for the response
        provider_map = [
            {
                "id": provider['id'],  # Provider's ID
                "descriptor": {
                    "name": provider['descriptor']['name'],
                    "images": provider['descriptor']['images']
                }
            } for provider in stored_data['message']['catalog']['providers']
        ]

        selected_fulfillment = next(
            (fulfillment for fulfillment in selected_provider['fulfillments']
             if fulfillment['id'] in selected_item['fulfillment_ids']), None)

        data = selected_fulfillment
        route_info_tag = data['tags'][
            0]  # Access the first (and only) tag in the 'tags' list
        tag_list = route_info_tag['list']
        route_id = next(item['value'] for item in tag_list if
                        item['descriptor']['code'] == 'ROUTE_ID')

        stops = data.get("stops", [])
        vehicle_variant = data.get("vehicle", []).get("variant")

        start_stop_code = stops[0]["location"]["descriptor"]["code"]
        end_stop_code = stops[-1]["location"]["descriptor"]["code"]

        fare = FareCalculator().get_fare_for_route(start_stop_code, end_stop_code,
                                                   route_id, vehicle_variant)

        base_fare = fare['bf']
        toll = fare['tl']
        message_data = on_select_request.get('item')
        selected_item['quantity'] = message_data[0]['quantity']
        discounted_fare = float(selected_item['price']['value']) + toll

        # Construct the formatted JSON response
        formatted_json_response = {
            "context": context_data,
            "message": {
                "order": {
                    "items": [selected_item],
                    "provider": provider_map[0],
                    "fulfillments": [fulfillment for fulfillment in
                                     selected_provider['fulfillments'] if
                                     fulfillment['id'] in selected_item[
                                         'fulfillment_ids']],
                    "quote": {
                        "price": {
                            "value": str(float(discounted_fare)),
                            "currency": selected_item['price']['currency']
                        },
                        "breakup": [{
                            "title": "BASE_FARE",
                            "item": {"id": request_item_id,
                                     "price": {
                                         "currency": selected_item['price']['currency'],
                                         "value": f"{base_fare}"
                                     },
                                     "quantity": {"selected": {"count": request_secected_count}}
                                     },
                            "price": {
                                "currency": selected_item['price']['currency'],
                                "value": f"{base_fare}"
                            }
                        },
                            {
                                "title": "TOLL",
                                "price": {
                                    "currency": selected_item['price']['currency'],
                                    "value": f"{toll}"
                                }
                            },
                        ]
                    }
                }
            }
        }

        # Update the data in Redis
        cache_key = f'{transaction_id}:select'
        cache.set(cache_key, formatted_json_response, timeout=CACHE_TIMEOUT)
        # print(f"Get select cached data======{cache_key}======{cache.get(cache_key)}")
        # For debugging
        logging.info(f"on_select payload JSON============: {formatted_json_response}")  # For debugging

        if bap_uri:
            logging.info(f"Posting select to BAP URI===: {bap_uri}")
            on_select_start_time_cache_key = (
                f"{transaction_id}:{CACHE_DELIMITER}:on_select_start_time")

            cache.set(on_select_start_time_cache_key, formatted_current_utc,
                      timeout=TIMESTAMP_CACHE_TIMEOUT)

            status_code, post_result = post_request(bap_uri, formatted_json_response)
            logging.info(f"on_select Response from BAP=====status_code:=={status_code}==txn_id:==={transaction_id}:===response:==== {post_result}")
            action = context_data['action']
            task_push_txn_logs.apply_async(args=[action, formatted_json_response])
            return True
        else:
            logging.error("BAP URI not found. in on_select")

    except Exception as e:
        logging.error(f"Unexpected error in on_select {on_select_request}: {str(e)}")
        return {'error': f"Unexpected error in on_select {on_select_request}: {str(e)}"}
