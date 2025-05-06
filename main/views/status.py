import requests
from django.http import HttpRequest
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet


# TODO: placeholder, remove it
class OnSelectRequestSerializer:
    pass


URL = "https://api.chartr.me/v1/webhook"


# The customer wants to status a particular route
class Status(GenericViewSet):

    def post(self, request):
        '''
        Request format:
            jsons/status_jsons/request.json
        Response format:
            jsons/status_jsons/response.json
        '''

        if request.modified_data['context']['action'] != "status":
            ...
            # throw error

        # if not request.body['message'].get('order_id', None):
        #     ...
        #     # throw error

        serializer = OnSelectRequestSerializer(data=request.modified_data['message'])
        if not serializer.is_valid():
            errors = serializer.errors
            raise ValidationError(errors)

        # call on_search to publish results
        on_status_request = HttpRequest()
        on_status_request.body = {
            "context": serializer.validated_data['context'],
            "order_id": serializer.validated_data['order_id']
        }
        self.on_status(on_status_request)

        # Send a ACK response
        response = {}

        return Response(response, status=200)

    def on_status(self, on_status_request):
        # makes the request to BAP
        '''
        Request format:
            jsons/on_status_jsons/request.json
        Response format:
            jsons/on_status_jsons/response.json
        '''

        # Getting the mandatory fields
        '''
            format of order_id:
            "O1"
        '''
        order_id = on_status_request.body['order_id']

        # TODO: call chartr API to status the route

        webhook_body = {
            "context": {
                "action": "on_status",
                # rest of the fields on_status_request.body['context]
            },
            "message": {
                "order": {
                    "id": order_id,
                    "status": "CONFIRMED",
                    "items": [
                        {
                            "id": item['id'],
                            "descriptor": {
                                "name": "",
                                "code": "",
                                "images": [
                                    {
                                        "url": ""
                                    }
                                ]
                            },
                            "price": {
                                "currency": "INR",
                                "value": ""
                            },
                            "quantity": {
                                "selected": {
                                    "count": 2
                                }
                            },
                            "fulfillment_ids": [
                                "F1"
                            ]
                        }
                        for item in order['items']
                    ],
                    "provider": {
                        "id": "P1",  # order['provider']['id'],
                        "descriptor": {
                            "name": "",
                            "images": [
                                {
                                    "url": ""
                                }
                            ]
                        },
                    },
                    "billing": {
                        "name": "John Doe",  # order['billing']['name'],
                        "email": "",  # order['billing']['email'],
                        "phone": "",  # order['billing']['phone'],
                    },
                    "quote": {
                        "price": {
                            "value": "",
                            "currency": "INR"
                        },
                        "breakup": [
                            {
                                "title": "Base Fare",
                                "item": {
                                    "id": "I1",  # item['id']
                                },
                                "price": {
                                    "currency": "INR",
                                    "value": ""
                                }
                            }
                            for item in order['items']
                        ]
                    },
                    "payements": [
                        {
                            "id": "P1",
                            "collected_by": "BAP",
                            "status": "NOT-PAID",
                            "type": "PRE-ORDER",
                            "params": {
                                "transaction_id": "",
                                "currency": "INR",
                                "amount": "",
                                "bank_code": "",
                                "bank_account_number": "",
                                "virtual_payment_address": "",
                            },
                        }
                    ],
                    "cancellation_terms": {
                        "cancel_by": {
                            "duration": ""
                        },  # Duration for cancellation of order
                        "cancellation_fee": {
                            "percentage": "",
                        }
                    }
                }
            }
        }
        response = requests.post(URL, json=webhook_body)
        # ping the BAP on_status API
        # get the response

        # TODO: Webhook

        return
