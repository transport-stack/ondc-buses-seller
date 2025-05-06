import logging

from main.constants import on_init_payment_parms
from modules.confirm_response_generator import increment_f_string
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


def pass_construct_final_json(stored_data, confirm_request_json, ticket_info, formatted_ticket_validity, ticket_id, formatted_created_at, variant):
    context = confirm_request_json['context']
    order = stored_data['message']['order']
    context['action'] = "on_confirm"

    items = order['items']
    fulfilllment_id = items[0]['fulfillment_ids'][0]

    provider_info = order["provider"]['id']
    provider_name = order["provider"]['descriptor']
    billing_info = order['billing']

    provider = {
        "id": provider_info,
        "descriptor": provider_name
    }

    authorization_info = {"type": "QR", "token": ticket_info,
                          "valid_to": formatted_ticket_validity,
                          "status": "CLAIMED"}

    fulfillments = [
        {
            "id": increment_f_string(fulfilllment_id),
            "type": "PASS",
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
                    "descriptor": {"code": "PASS_INFO"},
                    "list": [
                        {"descriptor": {"code": "NUMBER"}, "value": ticket_id},
                    ]
                }
            ]
        }
    ]

    payments = confirm_request_json["message"]["order"]["payments"]
    for payment in payments:
        if payment['id'] == 'PA1':  # Targeting specific payment ID; adjust as necessary
            payment['params'].update(on_init_payment_parms)

    final_json = {
        "context": context,
        "message": {
            "order": {
                "id": "01",
                "status": "ACTIVE",
                "items": items,
                "provider": provider,
                "fulfillments": fulfillments,
                "cancellation_terms": [{"cancel_by": {"duration": "PT60M"},
                                        "cancellation_fee": {"percentage": "0"}}],
                "billing": billing_info,
                "quote": order['quote'],
                "payments": payments,
                "created_at": formatted_created_at,
                "updated_at": formatted_created_at
            }
        }
    }

    return final_json
