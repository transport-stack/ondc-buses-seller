import logging
import os
import secrets
from datetime import datetime, timedelta

import pytz
import requests
from celery import shared_task
from django.core.cache import cache

from main.constants import CACHE_TIMEOUT, CACHE_DELIMITER, TIMESTAMP_CACHE_TIMEOUT, PINK_TICKET_FARE, DTC_FULL, DIMTS_FULL
from main.models.tickets import ClaimStatus
from main.utils.post_request import post_request
from main.utils.time_parser import get_current_utc_timestamp
from modules.confirm_response_generator import construct_final_json
from modules.create_ticket.main import TicketAndFareSetup
from modules.fare_setup.main import FareCalculator
from modules.get_bus_details import fetch_vehicle_data
from modules.ticket_string_generator.main import json_to_base64, encrypt_with_salt
from main.tasks.task_send_no import task_push_txn_logs

IST = pytz.timezone('Asia/Kolkata')


def create_new_ticket_id():
    date = (datetime.today().strftime('%d,%m,%Y')).split(',')
    ticket_id = 'T' + date[0] + date[1] + date[2] + str(secrets.token_hex(5))
    return ticket_id


def get_next_day_x_time(x=3):
    today_ist = datetime.now(IST)
    tomorrow_ist = today_ist + timedelta(days=1)
    tomorrow_ist_3am = tomorrow_ist.replace(hour=x, minute=0, second=0)
    tomorrow_ist_3am_wo_T = datetime.strftime(
        tomorrow_ist_3am, "%Y-%m-%dT%H:%M:%S"
    ).replace("T", " ")

    return tomorrow_ist_3am


@shared_task(name="main.tasks.on_confirm")
def on_confirm(on_confirm_request):
    try:
        context_data = on_confirm_request.get('context')
        formatted_current_utc = get_current_utc_timestamp()
        context_data['timestamp'] = formatted_current_utc
        context_data['action'] = "on_confirm"

        request_message_data = on_confirm_request.get('message')
        transaction_id = context_data['transaction_id']
        bap_uri = context_data['bap_uri'] + '/on_confirm'
        subscriber_id = context_data['bap_id']

        stored_data = cache.get(transaction_id + ':init')

        if not stored_data or not request_message_data['order']:
            raise Exception("No data found for the given transaction ID")

        route_id = \
            stored_data['message']['order']['fulfillments'][0]['tags'][0]['list'][0][
                'value']
        route_name = stored_data['message']['order']['items'][0]['descriptor']['name']
        provider_name = stored_data['message']['order']['provider']['descriptor']['name']
        provider_name = 'dtc' if provider_name == DTC_FULL else 'dimts' if provider_name == DIMTS_FULL else 'Unknown'
        variant = stored_data['message']['order']['fulfillments'][0]['vehicle']['variant']
        start_stop_code = stored_data['message']['order']['fulfillments'][0]['stops'][0]['location']['descriptor']['code']
        end_stop_code = stored_data['message']['order']['fulfillments'][0]['stops'][-1]['location']['descriptor']['code']
        start_stop_name = stored_data['message']['order']['fulfillments'][0]['stops'][0]['location']['descriptor']['name']
        end_stop_name = stored_data['message']['order']['fulfillments'][0]['stops'][-1]['location']['descriptor']['name']
        bus_reg_number = stored_data.get('message', {}).get('order', {}).get('fulfillments', [])[0].get('vehicle', {}).get('registration', None)
        pnr = request_message_data['order']['payments'][0]['params']['transaction_id']

        agency = provider_name
        ac = variant

        ticket_count = request_message_data['order']['items'][0]['quantity']['selected']['count']
        ticket_status = 1 if request_message_data['order']['payments'][0]['status'] == "PAID" else 0
        ticket_category = stored_data['message']['order']['items'][0]['descriptor']['code']
        data = stored_data['message']['order']['quote']
        toll = 0
        discount = 0
        basic = 0
        for item in data['breakup']:
            if item['title'] == 'BASE_FARE':
                basic = float(item['price']['value'])
            elif item['title'] == 'TOLL':
                toll = float(item['price']['value'])
            elif item['title'] == 'OFFER':
                discount = float(item['price']['value'])

        toll_per_ticket = toll / ticket_count

        discount_percent = (discount / basic) * 100

        ticket_id = create_new_ticket_id()
        ticket_validity = get_next_day_x_time(3).strftime("%Y-%m-%dT%H:%M:%S")
        ticket_created_at = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        formatted_created_at = ticket_created_at + 'Z'
        formatted_ticket_validity = ticket_validity + 'Z'   # datetime.strptime(ticket_validity, "%Y-%m-%dT%H:%M:%S.%f%z")
        category = "G"
        fare_per_ticket = toll_per_ticket + float(data['breakup'][0]['item']['price']['value'])  # toll + price of 1 ticket
        total_fare = toll + float(data['breakup'][0]['price']['value'])  # toll + price
        amount_payable_by_user = float(data['price']['value'])  # discounted amount

        qr_generator_data = (
                f"{ticket_created_at}#"
                f"ticket#{pnr}#"
                f"{route_name}#"
                f"{start_stop_name}#"
                f"{end_stop_name}#"
                f"{bus_reg_number}#"
                f"{ticket_validity}#"
                f"{ticket_id}#"
                f"{fare_per_ticket}#"
                f"{ticket_count}#"
                f"{agency}"
            )
        ticket_info = encrypt_with_salt(qr_generator_data)
        formatted_json_response = construct_final_json(stored_data, on_confirm_request,
                                                       ticket_info, formatted_ticket_validity,
                                                       ticket_id, formatted_created_at, bus_reg_number, ac)

        otp_response_redis_key = request_message_data['order']['payments'][0]['params'][
                                     'transaction_id'] + ':otp'
        cache.set(otp_response_redis_key, formatted_json_response,
                  timeout=CACHE_TIMEOUT)

        final_response_redis_key = context_data['transaction_id'] + ':confirm'
        cache.set(final_response_redis_key, formatted_json_response,
                  timeout=CACHE_TIMEOUT)

        if bap_uri:
            confirm_start_time_cache_key = (
                f"{transaction_id}:{CACHE_DELIMITER}:on_confirm_start_time")

            cache.set(confirm_start_time_cache_key, formatted_current_utc,
                      timeout=TIMESTAMP_CACHE_TIMEOUT)
            # confirm_timestamp_data = cache.get(confirm_start_time_cache_key)
            # logging.info(f"confirm_timestamp_data==========: {confirm_timestamp_data}")
            create_fare_breakup = TicketAndFareSetup().create_fare_breakup(
                basic=basic, amount=amount_payable_by_user, toll=toll,
                convenience_charge=0.0, convenience_charge_tax=0.0,
                franchisee_service_charge=0.0, discount=discount_percent,
                add_on=0.0, add_on_tax=0.0, cancellation_chg=0.0,
                coupon=0.0, coupon_discount=discount
            )
            # logging.info(f"Fare breakup created=====: {create_fare_breakup}")
            # logging.info(f"Claim Status======={type(bus_reg_number)}: {ClaimStatus.UNCLAIMED if bus_reg_number == 'None' else ClaimStatus.CLAIMED}")
            created_ticket = TicketAndFareSetup().create_ticket(
                pnr=pnr, ticket_status=ticket_status,
                transit_pnr=ticket_id, ticket_type_id=1 if category == "G" else 2,
                passenger_count=ticket_count, amount=amount_payable_by_user,
                payment_type=1, payment_status=3,
                fare=create_fare_breakup,
                valid_till=ticket_validity,
                vehicle_number=bus_reg_number,
                agency=agency.upper() if agency is not None else None,
                start_stop_name=start_stop_name,
                start_stop_code=start_stop_code,
                end_stop_name=end_stop_name,
                end_stop_code=end_stop_code,
                route=route_name,
                subscriber_id=subscriber_id,
                is_ac=True if ac.lower() == "ac" else False,
                description="Ticket",
                claim_status=ClaimStatus.CLAIMED
            )
            logging.info(f"on_confirm payload JSON============: {formatted_json_response}")
            status_code, post_result = post_request(bap_uri, formatted_json_response)
            logging.info(f"CONFIRM Response from BAP=====status_code:=={status_code}==txn_id:==={transaction_id}:===response:==== {post_result}")
            action = context_data['action']
            task_push_txn_logs.apply_async(args=[action, formatted_json_response])
        else:
            logging.error("BAP URI not found. in on_confirm")

    except Exception as e:
        logging.error(f"Unexpected error in on_confirm {on_confirm_request}: {str(e)}")
        return {'error': f"Unexpected error in on_confirm {on_confirm_request}: {str(e)}"}
