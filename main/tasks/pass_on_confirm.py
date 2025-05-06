import logging
import secrets
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import pytz
from celery import shared_task
from django.core.cache import cache
from main.constants import CACHE_TIMEOUT, CACHE_DELIMITER, TIMESTAMP_CACHE_TIMEOUT, DTC_FULL
from main.models import PassType
from main.models.tickets import ClaimStatus
from main.utils.post_request import post_request
from main.utils.time_parser import get_current_utc_timestamp
from modules.create_pass.main import PassAndPassFareSetup
from modules.pass_confirm_response_generator import pass_construct_final_json
from modules.ticket_string_generator.main import json_to_base64, encrypt_with_salt
from main.tasks.task_send_no import task_push_txn_logs

IST = pytz.timezone('Asia/Kolkata')


def create_new_ticket_id(pass_type):
    date = (datetime.today().strftime('%d,%m,%Y')).split(',')
    if pass_type == 'daily':
        ticket_id = 'DP' + date[0] + date[1] + date[2] + str(secrets.token_hex(5))
    elif pass_type == 'weekly':
        ticket_id = 'WP' + date[0] + date[1] + date[2] + str(secrets.token_hex(5))
    elif pass_type == 'monthly':
        ticket_id = 'MP' + date[0] + date[1] + date[2] + str(secrets.token_hex(5))
    else:
        raise ValueError("Invalid pass_type. Expected 'daily', 'weekly', or 'monthly'.")
    return ticket_id


def get_next_day_x_time(days=1, hour=0, minute=0, second=0):
    current_time_ist = datetime.now(IST)
    target_time_ist = current_time_ist + timedelta(days=days)
    target_time_ist = target_time_ist.replace(hour=hour, minute=minute, second=second, microsecond=0)
    target_time_str = datetime.strftime(target_time_ist, "%Y-%m-%d %H:%M:%S").replace("T", " ")
    return target_time_str


def get_pass_validity(pass_type="daily", created_at=None):
    if created_at is None:
        created_at = datetime.now(pytz.utc)

    created_at = created_at.astimezone(IST)
    print("created_at========", created_at)

    if pass_type == "daily":
        # Daily pass: valid till 23:59:59 of the same day
        valid_till = created_at.replace(hour=23, minute=59, second=59, microsecond=0)
    elif pass_type == "weekly":
        # Weekly pass: valid for 7 days from the created_at date
        valid_till = created_at + timedelta(weeks=1)
        valid_till = valid_till.replace(hour=23, minute=59, second=59, microsecond=0)
    elif pass_type == "monthly":
        # Monthly pass: valid till the same day of next month
        valid_till = created_at + relativedelta(days=29)
        valid_till = valid_till.replace(hour=23, minute=59, second=59, microsecond=0)
    else:
        raise ValueError("Invalid pass_type. Expected 'daily', 'weekly', or 'monthly'.")

    return valid_till.strftime("%Y-%m-%dT%H:%M:%S")


@shared_task(name="main.tasks.pass_on_confirm")
def pass_on_confirm(on_confirm_request):
    try:
        context_data = on_confirm_request.get('context')
        formatted_current_utc = get_current_utc_timestamp()
        context_data['timestamp'] = formatted_current_utc
        context_data['action'] = "on_confirm"

        request_message_data = on_confirm_request.get('message')
        transaction_id = context_data['transaction_id']
        bap_uri = context_data['bap_uri'] + '/on_confirm'
        subscriber_id = context_data['bap_id']

        stored_data = cache.get(transaction_id + ':pass_init')

        if not stored_data or not request_message_data['order']:
            raise Exception("No data found for the given transaction ID")

        provider_name = stored_data['message']['order']['provider']['descriptor']['name']
        provider_name = 'dtc' if provider_name == DTC_FULL else None
        variant = stored_data['message']['order']['fulfillments'][0]['vehicle']['variant']
        pnr = request_message_data['order']['payments'][0]['params']['transaction_id']
        pass_name = stored_data['message']['order']['items'][0]['descriptor']['name']
        pass_description = stored_data['message']['order']['items'][0]['descriptor']['short_desc']
        pass_status = 1 if request_message_data['order']['payments'][0]['status'] == "PAID" else 0
        data = stored_data['message']['order']['quote']
        basic = 0
        for item in data['breakup']:
            if item['title'] == 'BASE_FARE':
                basic = float(item['price']['value'])

        pass_type_name = PassType.objects.get(name=pass_name).pass_type

        pass_id = create_new_ticket_id(pass_type_name.lower())
        pass_validity = get_pass_validity(pass_type_name.lower())
        pass_created_at = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        formatted_created_at = pass_created_at + 'Z'
        formatted_ticket_validity = pass_validity + 'Z'
        amount_payable_by_user = float(data['price']['value'])
        customer_details = stored_data['message']['order']['fulfillments'][0]['customer']['person']
        user_details = {
            "name": stored_data['message']['order']['billing']['name'],
            "phone_number": stored_data['message']['order']['billing']['phone'],
            "email": stored_data['message']['order']['billing'].get('email', None),
            "govt_id": customer_details['creds'][0]['type'],
            "govt_id_number": customer_details['creds'][0]['id'],
            "photo": customer_details['image']['url']
        }

        qr_generator_data = (
        f"{pass_created_at}#"
        f"pass#{pnr}#{provider_name}#"
        f"{user_details['name']}#{user_details['phone_number']}#"
        f"{user_details['govt_id']}#{user_details['govt_id_number']}#"
        f"{pass_name}#{pass_description}#{pass_id}#"
        f"{pass_validity}#{amount_payable_by_user}"
    )
        ticket_info = encrypt_with_salt(qr_generator_data)
        formatted_json_response = pass_construct_final_json(stored_data, on_confirm_request, ticket_info, formatted_ticket_validity,
                                                            pass_id, formatted_created_at, variant)

        otp_response_redis_key = request_message_data['order']['payments'][0]['params'][
                                     'transaction_id'] + ':otp'
        cache.set(otp_response_redis_key, formatted_json_response,
                  timeout=CACHE_TIMEOUT)

        final_response_redis_key = context_data['transaction_id'] + ':confirm'
        cache.set(final_response_redis_key, formatted_json_response,
                  timeout=CACHE_TIMEOUT)

        if bap_uri:
            confirm_start_time_cache_key = (
                f"{transaction_id}:{CACHE_DELIMITER}:pass_on_confirm_start_time")

            cache.set(confirm_start_time_cache_key, formatted_current_utc,
                      timeout=TIMESTAMP_CACHE_TIMEOUT)
            confirm_timestamp_data = cache.get(confirm_start_time_cache_key)
            create_fare_breakup = PassAndPassFareSetup().create_pass_fare_breakup(
                basic=basic, amount=amount_payable_by_user, toll=0.0,
                convenience_charge=0.0, convenience_charge_tax=0.0,
                franchisee_service_charge=0.0, discount=0.0,
                add_on=0.0, add_on_tax=0.0, cancellation_chg=0.0,
                coupon=0.0, coupon_discount=0.0
            )
            created_pass = PassAndPassFareSetup().create_pass(
                pnr=pnr,
                pass_status=pass_status,
                transit_pnr=pass_id,
                pass_name=pass_name,
                fare=create_fare_breakup,
                valid_till=pass_validity,
                agency=provider_name.upper() if provider_name is not None else None,
                subscriber_id=subscriber_id,
                is_ac=True if variant.lower() == "ac" else False,
                claim_status=ClaimStatus.UNCLAIMED,
                amount=amount_payable_by_user,
                user_details=user_details
            )
            logging.info(f"pass_on_confirm payload JSON============: {formatted_json_response}")
            status_code, post_result = post_request(bap_uri, formatted_json_response)
            action = context_data['action']
            task_push_txn_logs.apply_async(args=[action, formatted_json_response])
            logging.info(f"pass_on_confirm response from BAP=====status_code:=={status_code}==txn_id:==={transaction_id}:===response:==== {post_result}")
        else:
            logging.error("BAP URI not found in pass_on_confirm")

    except Exception as e:
        logging.error(f"Unexpected error in pass_on_confirm: {str(e)}")
