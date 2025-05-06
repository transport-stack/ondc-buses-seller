import json
import logging
import os
from main.constants import payments_array, ROUTES_STOP_DATA_CACHE_TIMEOUT, DocumentEnums
from main.models import PassType
from main.utils.time_parser import get_current_utc_timestamp
from django.core.cache import cache
from django.db import IntegrityError


def on_search_1_page1(context, total_page_count):
    try:
        bap_uri = context['bap_uri']
        bap_id = context['bap_id']
        transaction_id = context.get('transaction_id')
        message_id = context.get('message_id')
        bpp_id = os.environ.get('BPP_ID')
        bpp_uri = os.environ.get('BPP_URL')
        formatted_current_utc = get_current_utc_timestamp()

        page1_payload = {
            "context": {
                    "location": {
                        "country": {"code": "IND"},
                        "city": {"code": "std:011"}
                    },
                    "domain": "ONDC:TRV11",
                    "action": "on_search",
                    "version": "2.0.1",
                    "bap_id": bap_id,
                    "bap_uri": bap_uri,
                    "bpp_id": bpp_id,
                    "bpp_uri": bpp_uri,
                    "transaction_id": transaction_id,
                    "message_id": message_id,
                    "timestamp": formatted_current_utc,
                    "ttl": "PT30S"
                },
            "message": {
                "catalog": {
                    "descriptor": {
                        "name": "Transit Solutions",
                        "images": [
                            {
                                "url": "https://transitsolutions.in/logos/logo.ico",
                                "size_type": "xs"
                            }
                        ]
                    },
                    "providers": [
                        {
                            "id": "P1",
                            "descriptor": {
                                "name": "Delhi Transport Corporation",
                                "images": [
                                    {
                                        "url": "https://dtc.delhi.gov.in/sites/default/files/DTC/logo/dtc_logo_2.png",
                                        "size_type": "xs"
                                    }
                                ]
                            },
                            "fulfillments": [
                                {
                                    "id": "F1",
                                    "type": "PASS",
                                    "stops": [
                                        {
                                            "type": "START",
                                            "location": {
                                                "descriptor": {
                                                    "code": "std:011"
                                                },
                                                "gps": "28.666576, 77.233332"
                                            },
                                            "id": "1"
                                        }
                                    ],
                                    "vehicle": {
                                        "category": "BUS",
                                        "variant": "NON_AC"
                                    },
                                    "customer":
                                        {
                                            "person": {
                                                "creds": [
                                                    {
                                                        "type": DocumentEnums.AAADHAR_CARD
                                                    },
                                                    {
                                                        "type": DocumentEnums.PAN_CARD
                                                    },
                                                    {
                                                        "type": DocumentEnums.DRIVING_LICENSE
                                                    },
                                                    {
                                                        "type": DocumentEnums.VOTER_ID_CARD
                                                    }
                                                ],
                                            },
                                        }
                                },
                                {
                                    "id": "F2",
                                    "type": "PASS",
                                    "stops": [
                                        {
                                            "type": "START",
                                            "location": {
                                                "descriptor": {
                                                    "code": "std:011"
                                                },
                                                "gps": "28.666576, 77.233332"
                                            },
                                            "id": "1"
                                        }
                                    ],
                                    "vehicle": {
                                        "category": "BUS",
                                        "variant": "AC"
                                    },
                                    "customer":
                                        {
                                            "person": {
                                                "creds": [
                                                    {
                                                        "type": DocumentEnums.AAADHAR_CARD
                                                    },
                                                    {
                                                        "type": DocumentEnums.PAN_CARD
                                                    },
                                                    {
                                                        "type": DocumentEnums.DRIVING_LICENSE
                                                    },
                                                    {
                                                        "type": DocumentEnums.VOTER_ID_CARD
                                                    },

                                                ],
                                            },
                                        }
                                }
                            ],
                            "items": [
                                {
                                    "id": "I1-SJT",
                                    "descriptor": {
                                        "name": "Single Journey Ticket",
                                        "code": "SJT",
                                        "images": [
                                            {
                                                "url": "https://dtc.delhi.gov.in/sites/default/files/DTC/logo/dtc_logo_2.png",
                                                "size_type": "xs"
                                            }
                                        ]
                                    },
                                    "time": {
                                        "label": "Validity",
                                        "duration": "PT1D",
                                        "timestamp": "2021-03-23T11:01:40.065Z"
                                    }
                                },
                                {
                                    "id": "I2-SFSJT",
                                    "descriptor": {
                                        "name": "Special Fair Single Journey Ticket",
                                        "code": "SFSJT",
                                        "images": [
                                            {
                                                "url": "https://dtc.delhi.gov.in/sites/default/files/DTC/logo/dtc_logo_2.png",
                                                "size_type": "xs"
                                            }
                                        ]
                                    },
                                    "time": {
                                        "label": "Validity",
                                        "duration": "PT1D",
                                        "timestamp": "2021-03-23T11:01:40.065Z"
                                    }
                                },
                                {
                                    "id": "I3-DAILY-PASS",
                                    "descriptor": {
                                        "name": "DAILY ALL ROUTE NON AC PASS",
                                        "short_desc": "Daily non-ac bus pass for all routes",
                                        "code": "PASS",
                                        "images": [
                                            {
                                                "url": "https://dtc.delhi.gov.in/sites/default/files/DTC/logo/dtc_logo_2.png",
                                                "size_type": "xs"
                                            }
                                        ]
                                    },
                                    "fulfillment_ids": [
                                        "F1"
                                    ],
                                    "price": {
                                        "currency": "INR",
                                        "value": "40"
                                    },
                                    "quantity": {
                                        "maximum": {
                                            "count": 1
                                        },
                                        "minimum": {
                                            "count": 1
                                        }
                                    },
                                    "time": {
                                        "label": "Validity",
                                        "duration": "PT1D"
                                    }
                                },
                                {
                                    "id": "I4-DAILY-PASS",
                                    "descriptor": {
                                        "name": "DAILY ALL ROUTE AC PASS",
                                        "short_desc": "Daily ac bus pass for all routes",
                                        "code": "PASS",
                                        "images": [
                                            {
                                                "url": "https://dtc.delhi.gov.in/sites/default/files/DTC/logo/dtc_logo_2.png",
                                                "size_type": "xs"
                                            }
                                        ]
                                    },
                                    "fulfillment_ids": [
                                        "F2"
                                    ],
                                    "price": {
                                        "currency": "INR",
                                        "value": "50"
                                    },
                                    "quantity": {
                                        "maximum": {
                                            "count": 1
                                        },
                                        "minimum": {
                                            "count": 1
                                        }
                                    },
                                    "time": {
                                        "label": "Validity",
                                        "duration": "PT1D"
                                    }
                                },
                                {
                                    "id": "I5-MONTHLY-PASS",
                                    "descriptor": {
                                        "name": "MONTHLY GENERAL ALL ROUTE NON AC PASS",
                                        "short_desc": "Monthly non-ac bus pass for all routes",
                                        "code": "PASS",
                                        "images": [
                                            {
                                                "url": "https://dtc.delhi.gov.in/sites/default/files/DTC/logo/dtc_logo_2.png",
                                                "size_type": "xs"
                                            }
                                        ]
                                    },
                                    "fulfillment_ids": [
                                        "F1"
                                    ],
                                    "price": {
                                        "currency": "INR",
                                        "value": "800"
                                    },
                                    "quantity": {
                                        "maximum": {
                                            "count": 1
                                        },
                                        "minimum": {
                                            "count": 1
                                        }
                                    },
                                    "time": {
                                        "label": "Validity",
                                        "duration": "P1M"
                                    }
                                },
                                {
                                    "id": "I6-MONTHLY-PASS",
                                    "descriptor": {
                                        "name": "MONTHLY GENERAL ALL ROUTE AC PASS",
                                        "short_desc": "Monthly ac bus pass for all routes",
                                        "code": "PASS",
                                        "images": [
                                            {
                                                "url": "https://dtc.delhi.gov.in/sites/default/files/DTC/logo/dtc_logo_2.png",
                                                "size_type": "xs"
                                            }
                                        ]
                                    },
                                    "fulfillment_ids": [
                                        "F2"
                                    ],
                                    "price": {
                                        "currency": "INR",
                                        "value": "1000"
                                    },
                                    "quantity": {
                                        "maximum": {
                                            "count": 1
                                        },
                                        "minimum": {
                                            "count": 1
                                        }
                                    },
                                    "time": {
                                        "label": "Validity",
                                        "duration": "P1M"
                                    }
                                },
                                {
                                    "id": "I7-MONTHLY-PASS",
                                    "descriptor": {
                                        "name": "MONTHLY AIR PORT EXPRESS AC BUS PASS",
                                        "short_desc": "Monthly ac bus pass for airport express",
                                        "code": "PASS",
                                        "images": [
                                            {
                                                "url": "https://dtc.delhi.gov.in/sites/default/files/DTC/logo/dtc_logo_2.png",
                                                "size_type": "xs"
                                            }
                                        ]
                                    },
                                    "fulfillment_ids": [
                                        "F2"
                                    ],
                                    "price": {
                                        "currency": "INR",
                                        "value": "1400"
                                    },
                                    "quantity": {
                                        "maximum": {
                                            "count": 1
                                        },
                                        "minimum": {
                                            "count": 1
                                        }
                                    },
                                    "time": {
                                        "label": "Validity",
                                        "duration": "P1M"
                                    }
                                },
                                {
                                    "id": "I8-MONTHLY-PASS",
                                    "descriptor": {
                                        "name": "MONTHLY DELHI AND NCR AIR PORT AC BUS PASS",
                                        "short_desc": "Monthly ac bus pass for delhi and ncr airport",
                                        "code": "PASS",
                                        "images": [
                                            {
                                                "url": "https://dtc.delhi.gov.in/sites/default/files/DTC/logo/dtc_logo_2.png",
                                                "size_type": "xs"
                                            }
                                        ]
                                    },
                                    "fulfillment_ids": [
                                        "F2"
                                    ],
                                    "price": {
                                        "currency": "INR",
                                        "value": "1800"
                                    },
                                    "quantity": {
                                        "maximum": {
                                            "count": 1
                                        },
                                        "minimum": {
                                            "count": 1
                                        }
                                    },
                                    "time": {
                                        "label": "Validity",
                                        "duration": "P1M"
                                    }
                                }
                            ],
                            "payments": payments_array
                        },
                        {
                            "id": "P2",
                            "descriptor": {
                                "name": "Delhi Integrated Multi-Modal Transit System",
                                "images": [
                                    {
                                        "url": "https://www.dimts.in/images/logo.png",
                                        "size_type": "xs"
                                    }
                                ]
                            },
                            "items": [
                                {
                                    "id": "I9-SJT",
                                    "descriptor": {
                                        "name": "Single Journey Ticket",
                                        "code": "SJT",
                                        "images": [
                                            {
                                                "url": "https://www.dimts.in/images/logo.png",
                                                "size_type": "xs"
                                            }
                                        ]
                                    },
                                    "time": {
                                        "label": "Validity",
                                        "duration": "PT1D",
                                        "timestamp": "2021-03-23T11:01:40.065Z"
                                    }
                                },
                                {
                                    "id": "I10-SFSJT",
                                    "descriptor": {
                                        "name": "Special Fair Single Journey Ticket",
                                        "code": "SFSJT",
                                        "images": [
                                            {
                                                "url": "https://www.dimts.in/images/logo.png",
                                                "size_type": "xs"
                                            }
                                        ]
                                    },
                                    "time": {
                                        "label": "Validity",
                                        "duration": "PT1D",
                                        "timestamp": "2021-03-23T11:01:40.065Z"
                                    }
                                }
                            ],
                            "payments": payments_array
                        }
                    ],
                    "tags": [
                        {
                            "descriptor": {
                                "code": "PAGINATION",
                                "name": "Pagination"
                            },
                            "display": True,
                            "list": [
                                {
                                    "descriptor": {
                                        "code": "PAGINATION_ID"
                                    },
                                    "value": "P1"
                                },
                                {
                                    "descriptor": {
                                        "code": "MAX_PAGE_NUMBER"
                                    },
                                    "value": f"{total_page_count}"
                                }
                            ]
                        }
                    ]
                }
            }
        }
        CACHE_KEY_FIRST_PAGE = "on_search_1_first_page"
        cache.set(CACHE_KEY_FIRST_PAGE, page1_payload, timeout=None)
        data_dir = os.path.join('.', 'data')
        if not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)

        # Define the file path
        file_path = os.path.join(data_dir, "on_search_data.json")

        # Save JSON data to file
        # with open(file_path, "w", encoding="utf-8") as json_file:
        #     json_file.write(json.dumps(page1_payload, indent=4, ensure_ascii=False))


        items = page1_payload['message']['catalog']['providers'][0]['items']
        print("items=================", items)  # For testing purposes only

        passes = [item for item in items if item['descriptor'].get('code') == "PASS"]
        pass_names = [item['descriptor']['name'] for item in passes]
        existing_passes = PassType.objects.filter(name__in=pass_names).values_list('name', flat=True)
        print("existing_passes=================", existing_passes)  # For testing purposes only

        if len(existing_passes) == len(pass_names):
            logging.info("All pass types are already present in the database. Skipping insertion.")
        pk = 1
        for item in passes:
            name = item['descriptor'].get('name')
            description = item['descriptor'].get('short_desc', "")
            price = float(item['price']['value'])
            validity_duration = item['time']['duration']
            provider_id = page1_payload.get('message', {}).get('catalog', {}).get('providers', [{}])[0].get('id')
            item_id = item['id']
            fulfillment_id = item.get('fulfillment_ids', [{}])[0]

            fulfillments = page1_payload.get('message', {}).get('catalog', {}).get('providers', [{}])[0].get('fulfillments')
            variant = next((fulfillment['vehicle']['variant'] for fulfillment in fulfillments if fulfillment['id'] == fulfillment_id), "")
            creds_array = fulfillments[0].get('customer', {}).get('person', {}).get('creds', [{}])
            logging.info(f"creds_array========: {creds_array}")

            documents_array = []
            for creds in creds_array:
                if creds.get('type') in DocumentEnums.keys():
                    documents_array.append(DocumentEnums.get_value(creds.get('type')))

            # Extract validity in days from ISO 8601 duration (e.g., "P1M", "PT1D")
            if validity_duration.startswith("P"):
                validity_in_days = 30 if "M" in validity_duration else 1
            else:
                validity_in_days = 1  # Default to 1 day if format is unclear

            # Insert into PassType table
            try:
                pass_type, created = PassType.objects.get_or_create(
                    name=name,
                    defaults={
                        'pk': pk,
                        "description": description,
                        "validity_in_days": validity_in_days,
                        "pass_type": "MONTHLY" if validity_in_days == 30 else "WEEKLY" if validity_in_days == 7 else "DAILY",
                        "price": price,
                        "item_id": item_id,
                        "provider_id": provider_id,
                        "is_ac": True if variant == 'AC' else False,
                        "is_active": True,
                        "is_document_required": True if validity_in_days > 1 else False,
                        "allowed_documents": documents_array if validity_in_days > 1 else None
                    },
                )
                if created:
                    logging.info(f"Inserted new PassType: {name}")
                    pk += 1
                else:
                    logging.info(f"PassType already exists: {name}")

            except IntegrityError as e:
                logging.error(f"Error inserting PassType {name}: {e}")

        return page1_payload

    except Exception as e:
        logging.error(f"Error in on_search_1_page1: {e}")
        return {"status": "error", "message": str(e)}

