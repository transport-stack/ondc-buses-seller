import logging

from celery import shared_task
from django.core.cache import cache
from django.apps import apps
from main.constants import CACHE_DELIMITER, TIMESTAMP_CACHE_TIMEOUT
import requests
from main.utils.time_parser import get_current_utc_timestamp


@shared_task(name="main.tasks.on_receiver_recon")
def on_receiver_recon(on_receiver_recon_request):
    try:
        context_data = on_receiver_recon_request.get('context')
        message_data = on_receiver_recon_request.get('message')
        if not context_data or not message_data:
            logging.error("Invalid request: Missing 'context' or 'message' in the request.")
            return False

        transaction_id = context_data.get('transaction_id')
        bap_uri = context_data.get('bap_uri')
        if not transaction_id or not bap_uri:
            logging.error("Invalid context data: Missing 'transaction_id' or 'bap_uri'.")
            return False

        bap_uri += '/on_receiver_recon'

        context_data['action'] = "on_receiver_recon"
        context_data['ttl'] = "PT300S"
        formatted_current_utc = get_current_utc_timestamp()
        context_data['timestamp'] = formatted_current_utc
        orders = message_data['orderbook']['orders']
        order_array = []
        for order in orders:
            settlement_id = order['settlement_id']
            settlement_reference_no = order['settlement_reference_no']
            settlement_transaction_id = order['transaction_id']
            order_id = order['id']
            amount = order['payment']['params']['amount']
            settlement_reference = order['payment']['@ondc/org/settlement_details'][0]['settlement_reference']
            Ticket = apps.get_model('main', 'Ticket')
            ticket_exists = Ticket.objects.filter(transit_pnr=settlement_reference).exists()
            if not ticket_exists:
                order_array.append(
                    {
                        "collector_app_id": context_data['bap_id'],
                        "counterparty_diff_amount": {
                            "currency": "INR",
                            "value": amount
                        },
                        "counterparty_recon_status": "02",
                        "id": order_id,
                        "order_recon_status": "02",
                        "receiver_app_id": context_data['bpp_id'],
                        "settlement_id": settlement_id,
                        "settlement_reference_no": settlement_reference_no,
                        "transaction_id": settlement_transaction_id
                    }
                )

        on_receiver_recon_payload = {
            "context": context_data,
            "message": {
                "orderbook": {
                    "orders": order_array
                }
            }
        }
        on_receiver_recon_cache_key = f"{context_data['transaction_id']}:{CACHE_DELIMITER}:on_receiver_recon"
        cache.set(on_receiver_recon_cache_key, on_receiver_recon_payload, timeout=TIMESTAMP_CACHE_TIMEOUT)

        if bap_uri:
            logging.info(f"Posting to BAP URI: {bap_uri}")
            try:
                response = requests.post(bap_uri, json=on_receiver_recon_payload, headers={'X-Timestamp': formatted_current_utc})
                response.raise_for_status()
                logging.info(f"on_receiver_recon Response=====: {response.json()}")
                return True
            except requests.RequestException as e:
                logging.error(f"Error posting to BAP URI on_receiver_recon: {e}")
                return False
        else:
            logging.error("BAP URI not found. on_receiver_recon")
            return False
    except Exception as e:
        logging.error(f"Unexpected error in on_receiver_recon: {e}")
        return False
