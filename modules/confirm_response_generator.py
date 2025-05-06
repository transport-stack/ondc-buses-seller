import logging
import uuid

from main.constants import TICKET_NAME, TICKET_CODE, billing_info, on_init_payment_parms
from modules.fare_setup.main import static_bus_dict


def get_bus_number(data):
    try:
        # Define bus numbers for both corporations and conditions, with AC/NAC prefix for clarity

        # Navigate through the JSON to find the provider's name and air condition status
        provider_name = data["message"]["order"]["provider"]["descriptor"]["name"]
        air_condition = False  # Default value in case AIR_CONDITION tag is not found
        for tag in data["message"]["order"]["fulfillments"][0]["tags"]:
            if tag["descriptor"]["code"] == "ROUTE_INFO":
                for info in tag["list"]:
                    if info["descriptor"]["code"] == "AIR_CONDITION":
                        air_condition = info["value"]
                        break

        bus_number = static_bus_dict[provider_name]["AC"][
            "bus_reg_num"] if air_condition else \
            static_bus_dict[provider_name]["NAC"]["bus_reg_num"]

        return bus_number

    except KeyError as e:
        logging.error(f"Key not found in data: {e}")
        return None


def increment_f_string(s):
    # Extract the prefix (letters) and number
    prefix = s[:-1]  # All characters except the last one
    number = s[-1]   # The last character

    # Increment the number part
    incremented_number = str(int(number) + 1)

    # Combine the prefix and incremented number
    return f"{prefix}{incremented_number}"


def construct_final_json(stored_data, confirm_request_json, ticket_info, formatted_ticket_validity, ticket_id, formatted_created_at,
                         bus_reg_number, variant):
    context = confirm_request_json['context']
    order = stored_data['message']['order']
    context['action'] = "on_confirm"

    items = order['items']
    fulfilllment_id = items[0]['fulfillment_ids'][0]

    provider_info = order["provider"]['id']
    provider_name = order["provider"]['descriptor']

    provider = {
        "id": provider_info,
        "descriptor": provider_name
    }

    # Calculate the total price for use in the quote
    total_price = sum(float(item["price"]["value"]) for item in items)

    authorization_info = {"type": "QR", "token": ticket_info,
                          "valid_to": formatted_ticket_validity,
                          "status": "UNCLAIMED" if bus_reg_number is None else "CLAIMED"}

    fulfillments = [{
        "id": fulfilllment_id,
        "type": "TRIP",
        "stops": stored_data['message']['order']['fulfillments'][0]['stops'],
        "vehicle": {"category": "BUS", "variant": variant, "registration": bus_reg_number},
        "tags": [
            stored_data['message']['order']['fulfillments'][0]['tags'][0],
            {
                "descriptor": {"code": "TICKET_INFO"},
                "list": [
                    {"descriptor": {"code": "NUMBER"}, "value": ticket_id},
                ]
            }
        ]
    },
        {
            "id": increment_f_string(fulfilllment_id),
            "type": "TICKET",
            "stops": [
                {
                    "type": "START",
                    "authorization": authorization_info
                }
            ],
            "tags": [
                {
                    "descriptor": {
                        "code": "INFO"
                    },
                    "list": [
                        {
                            "descriptor": {
                                "code": "PARENT_ID"
                            },
                            "value": fulfilllment_id
                        }
                    ]
                },
                {
                    "descriptor": {"code": "TICKET_INFO"},
                    "list": [
                        {"descriptor": {"code": "NUMBER"}, "value": ticket_id},
                    ]
                }
            ]
        }
    ]

    start_stop = fulfillments[0]['stops'][0]

    if start_stop['type'] == 'START':
        keys = list(start_stop.keys())
        insert_index = keys.index('location') + 1
        keys.insert(insert_index, 'authorization')
        start_stop = {k: start_stop[k] if k != 'authorization' else authorization_info
                      for k in keys}
        fulfillments[0]['stops'][0] = start_stop

    payments = confirm_request_json["message"]["order"]["payments"]
    for payment in payments:
        if payment['id'] == 'PA1':  # Targeting specific payment ID; adjust as necessary
            payment['params'].update(on_init_payment_parms)

    final_json = {
        "context": context,
        "message": {
            "order": {
                "id": str(uuid.uuid4()),
                "status": "ACTIVE",
                "items": items,
                "provider": provider,
                "fulfillments": fulfillments,
                "cancellation_terms": [{"cancel_by": {"duration": "PT60M"},
                                        "cancellation_fee": {"percentage": "0"}}],
                "billing": billing_info['billing'],
                "quote": order['quote'],
                "payments": payments,
                "created_at": formatted_created_at,
                "updated_at": formatted_created_at
            }
        }
    }

    return final_json
