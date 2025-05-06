CACHE_TIMEOUT = 1800
TICKET_NAME = "Single Journey Ticket"
TICKET_CODE = "SJT"
GENERAL_TICKET_TYPE_ID = 1
GENERAL_PASS_TYPE_ID = 1
CACHE_DELIMITER = "seller"
TIMESTAMP_CACHE_TIMEOUT = 60
DISCOUNT = 0.10
MIN_PAX_COUNT = 1
MAX_PAX_COUNT = 3
PINK_TICKET_FARE = 10.0
ROUTES_STOP_DATA_CACHE_TIMEOUT = 24*60*60
DIMTS_FULL = 'Delhi Integrated Multi-Modal Transit System'
DTC_FULL = 'Delhi Transport Corporation'


class DocumentEnums:
    PAN_CARD = 'PAN'
    AAADHAR_CARD = 'AADHAR'
    VOTER_ID_CARD = 'VOTER_ID'
    DRIVING_LICENSE = 'DL'
    
    _enums = {
        'PAN': 'Pan Card',
        'AADHAR': 'Aadhar Card',
        'VOTER_ID': 'Voters ID Card',
        'DL': 'Driving Licence'
    }

    @classmethod
    def get_value(cls, key):
        return cls._enums.get(key)

    @classmethod
    def keys(cls):
        return cls._enums.keys()

    @classmethod
    def items(cls):
        return cls._enums.items()

def round_school(x):
    i, f = divmod(x, 1)
    return int(i + ((f >= 0.5) if (x > 0) else (f > 0.5)))


payments_array = [
                {
                    "collected_by": "BAP",
                    "tags": [
                        {
                            "descriptor": {
                                "code": "BUYER_FINDER_FEES"
                            },
                            "display": False,
                            "list": [
                                {
                                    "descriptor": {
                                        "code": "BUYER_FINDER_FEES_PERCENTAGE"
                                    },
                                    "value": "0"
                                },
                                {
                                    "descriptor": {
                                        "code": "BUYER_FINDER_FEES_TYPE"
                                    },
                                    "value": "percent-annualized"
                                }
                            ]
                        },
                        {
                            "descriptor": {
                                "code": "SETTLEMENT_TERMS"
                            },
                            "display": False,
                            "list": [
                                {
                                    "descriptor": {
                                        "code": "SETTLEMENT_WINDOW"
                                    },
                                    "value": "PT1D"
                                },
                                {
                                    "descriptor": {
                                        "code": "SETTLEMENT_BASIS"
                                    },
                                    "value": "INVOICE_RECEIPT"
                                },
                                {
                                    "descriptor": {
                                        "code": "MANDATORY_ARBITRATION"
                                    },
                                    "value": "TRUE"
                                },
                                {
                                    "descriptor": {
                                        "code": "COURT_JURISDICTION"
                                    },
                                    "value": "New Delhi"
                                },
                                {
                                    "descriptor": {
                                        "code": "STATIC_TERMS"
                                    },
                                    "value": "https://cdn-delhi.transportstack.in/ondc-seller/DTC_static_terms.pdf"
                                }
                            ]
                        }
                    ]
                }
            ]


billing_info = {
    "billing": {
        "name": "",
        "email": "",
        "phone": ""
    }
 }

cancellation_terms = [
            {
                "cancel_by": {"duration": "PT60M"},
                "cancellation_fee": {"percentage": "0"}
            }
        ]

on_init_payment_parms = {
            "bank_code": "CNRB0019126",
            "bank_account_number": "110039418119",
            "virtual_payment_address": "dummy5020@cnrb"
          }
