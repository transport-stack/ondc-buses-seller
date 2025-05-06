import logging
import requests
from celery import shared_task
from django.core.cache import cache

from main.constants import (CACHE_TIMEOUT, billing_info, cancellation_terms,
                            on_init_payment_parms, CACHE_DELIMITER,
                            TIMESTAMP_CACHE_TIMEOUT, DISCOUNT)
from main.utils.post_request import post_request
from main.utils.time_parser import get_current_utc_timestamp
from main.tasks.task_send_no import task_push_txn_logs


@shared_task(name="main.tasks.on_init")
def on_init(on_init_request, *args, **kwargs):
    try:
        context_data = on_init_request.get('context')

        formatted_current_utc = get_current_utc_timestamp()
        context_data['timestamp'] = formatted_current_utc
        context_data['action'] = "on_init"
        context_data['ttl'] = 'PT03M'

        request_message_data = on_init_request.get('message')
        transaction_id = context_data['transaction_id']
        bap_uri = context_data['bap_uri'] + '/on_init'

        stored_data = cache.get(f'{transaction_id}:select')
        passenger_count = request_message_data['order']['items'][0]['quantity']['selected']['count']

        if not stored_data or not request_message_data['order']:
            raise ValueError(f"No data found for the given transaction ID {transaction_id} inside on_init")

        formatted_json_response = {
            "context": context_data,
            "message": stored_data['message'],
        }
        payment_count = 1
        updated_payments = []
        for payment in request_message_data['order']['payments']:
            # Construct the new payment dictionary with additional 'params'
            new_payment = {
                'id': f'PA{payment_count}',  # Increment the payment count.
                'collected_by': payment['collected_by'],
                'status': payment['status'],
                'type': payment['type'],
                'params': on_init_payment_parms,
                'tags': payment['tags']
            }
            updated_payments.append(new_payment)

        message_section = formatted_json_response['message']['order']

        # Create a new dictionary to insert elements correctly
        new_message_order = {}
        for key, value in message_section.items():
            if key == "quote":
                new_message_order["cancellation_terms"] = cancellation_terms
                new_message_order.update(
                    billing_info)
                new_message_order[key] = value
                new_message_order[
                    "payments"] = updated_payments
            else:
                new_message_order[key] = value

        # Updating quotes
        quote = new_message_order['quote']

        # Updating the overall price
        quote['price']['value'] = float(quote['price']['value']) * passenger_count
        quote['price']['value'] = f"{quote['price']['value']}"

        # Updating the count in the first item of the breakup
        quote['breakup'][0]['item']['quantity']['selected']['count'] = passenger_count

        # Updating the price value of the first item in the breakup
        quote['breakup'][0]['price']['value'] = float(quote['breakup'][0]['price']['value']) * passenger_count
        quote['breakup'][0]['price']['value'] = f"{quote['breakup'][0]['price']['value']}"

        # Updating the count in the toll of the breakup
        quote['breakup'][1]['price']['value'] = float(quote['breakup'][1]['price']['value']) * passenger_count
        quote['breakup'][1]['price']['value'] = f"{quote['breakup'][1]['price']['value']}"

        # Updating Discount value
        quote['breakup'][-1]['price']['value'] = float(quote['breakup'][0]['price']['value']) * DISCOUNT
        quote['breakup'][-1]['price']['value'] = f"{quote['breakup'][-1]['price']['value']}"

        # Updating price and count in Items
        item = new_message_order['items'][0]
        # Updating the price value of the first item
        item['price']['value'] = float(item['price']['value']) * passenger_count
        item['price']['value'] = f"{item['price']['value']}"
        # Updating the count in the first item
        item['quantity']['selected']['count'] = passenger_count

        # Replace the old message section with the new one
        formatted_json_response['message']['order'] = new_message_order
        cache_key = context_data['transaction_id'] + ':init'
        cache.set(cache_key, formatted_json_response, timeout=CACHE_TIMEOUT)


        if bap_uri:
            on_init_start_time_cache_key = (
                f"{transaction_id}:{CACHE_DELIMITER}:on_init_start_time")

            cache.set(on_init_start_time_cache_key, formatted_current_utc,
                      timeout=TIMESTAMP_CACHE_TIMEOUT)
            logging.info(f"on_init payload JSON============: {formatted_json_response}")
            status_code, post_result = post_request(bap_uri, formatted_json_response)
            logging.info(f"INIT Response from BAP=====status_code:=={status_code}==txn_id:==={transaction_id}:===response:==== {post_result}")
            action = context_data['action']
            task_push_txn_logs.apply_async(args=[action, formatted_json_response])
            return True
        else:
            logging.error("BAP URI not found.")

    except Exception as e:
        logging.error(f"Unexpected error in on_init {on_init_request}: {str(e)}")
        return {'error': f"Unexpected error in on_init {on_init_request}: {str(e)}"}
