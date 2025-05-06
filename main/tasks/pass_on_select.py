import json
import logging
import os
from datetime import timezone, datetime, timedelta
from celery import shared_task
from django.core.cache import cache
from main.constants import CACHE_TIMEOUT, CACHE_DELIMITER, TIMESTAMP_CACHE_TIMEOUT, DocumentEnums
from main.models import PassType
from main.utils.post_request import post_request
from main.utils.time_parser import get_current_utc_timestamp
from main.tasks.task_send_no import task_push_txn_logs


@shared_task(name="main.tasks.pass_on_select")
# @profile_task
def pass_on_select(on_select_request):
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
        stored_data = cache.get('on_search_1_first_page')

        if not stored_data:
            logging.error("No on_search_1_data found in cache")

            # Define the path to the fallback JSON file
            data_dir = os.path.join('.', 'data')
            file_path = os.path.join(data_dir, "on_search_data.json")

            # Load data from the file if it exists
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as json_file:
                    stored_data = json.load(json_file)
                logging.info("on_search_1 data loaded successfully.")
            else:
                # If both cache and file are missing, return an error response
                logging.error(f"on_search_1 File not found: {file_path}")
                raise Exception("No Stored on_search_1_first_page Found")

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
        selected_pass = PassType.objects.get(item_id=request_item_id, provider_id=request_provider_id)
        base_fare = selected_pass.price
        validity_range = selected_pass.validity_in_days
        selected_item['time']['timestamp'] = formatted_current_utc
        selected_item['time']['range'] = {
            "start": formatted_current_utc,
            "end": (datetime.now(timezone.utc) + timedelta(days=validity_range)).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        }
        quantity = {
            "selected": {
                "count": request_secected_count
            }
        }
        selected_item['quantity'] = quantity
        fulfillment_obj = next(
            (fulfillment for fulfillment in selected_provider['fulfillments']
             if fulfillment['id'] in selected_item['fulfillment_ids']),
            None
        )
        # Construct the formatted JSON response
        formatted_json_response = {
            "context": context_data,
            "message": {
                "order": {
                    "items": [selected_item],
                    "provider": provider_map[0],
                    "fulfillments": [fulfillment_obj],
                    "quote": {
                        "price": {
                            "value": base_fare,
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
                                    "value": "0"
                                }
                            },
                            {
                                "title": "OFFER",
                                "price": {
                                    "currency": selected_item['price']['currency'],
                                    "value": "0"
                                }
                            }
                        ]
                    }
                }
            }
        }

        # Update the data in Redis
        cache_key = f'{transaction_id}:pass_select'
        cache.set(cache_key, formatted_json_response, timeout=CACHE_TIMEOUT)
        logging.info(f"pass_on_select payload JSON============: {formatted_json_response}")

        if bap_uri:
            logging.info(f"Posting to BAP URI: {bap_uri}")
            pass_on_select_start_time_cache_key = (
                f"{transaction_id}:{CACHE_DELIMITER}:pass_on_select_start_time")

            cache.set(pass_on_select_start_time_cache_key, formatted_current_utc,
                      timeout=TIMESTAMP_CACHE_TIMEOUT)

            status_code, post_result = post_request(bap_uri, formatted_json_response)
            action = context_data['action']
            task_push_txn_logs.apply_async(args=[action, formatted_json_response])
            logging.info(f"pass_on_select response from BAP=====status_code:=={status_code}==txn_id:==={transaction_id}:===response:==== {post_result}")
            return True
        else:
            logging.error("BAP URI not found pass_on_select.")

    except Exception as e:
        logging.error(f"Unexpected error pass_on_select: {str(e)}")
