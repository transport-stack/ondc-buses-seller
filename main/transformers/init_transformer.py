from main.models.request import (
    Item,
    Billing,
    Payment
)
from main.transformers.base import RequestBodyTransformer


class InitTransformer(RequestBodyTransformer):

    def chartr_to_ondc(self, item, billing, payment, *args, context=None, **kwargs):
        return {
            "context": context,
            "message": {
                "order": {
                    "items": [
                        {
                            "id": str(item.id),
                            "descriptor": {
                                "name": "sdfsd",
                                "code": "sdf",
                                "images": [
                                    {
                                        "url": "sdfsdf"
                                    }
                                ]
                            },
                            "price": {
                                "currency": "INR",
                                "value": str(item.price)
                            },
                            "quantity": {
                                "selected": {
                                    "count": item.quantity
                                }
                            },  # item['quantity'],
                            "fulfillment_ids": [
                                str(item.fulfillment.id)
                            ]
                        }
                    ],
                    "provider": {
                        "id": "P1",  # order['provider']['id'],
                        "descriptor": {
                            "name": "sdfsd",
                            "code": "sdf",
                            "images": [
                                {
                                    "url": "sdfsdf"
                                }
                            ]
                        },
                    },
                    "billing": {
                        "name": billing.name,  # order['billing']['name'],
                        "email": billing.email,  # order['billing']['email'],
                        "phone": billing.phone,  # order['billing']['phone'],
                    },
                    "quote": {
                        "price": {
                            "value": str(item.price),
                            "currency": "INR"
                        },
                        "breakup": [
                            {
                                "title": "Base Fare",
                                "item": {
                                    "id": str(item.id),  # item['id']
                                },
                                "price": {
                                    "currency": "INR",
                                    "value": str(item.price)
                                }
                            }
                        ]
                    },
                    "payments": [
                        {
                            "id": str(payment.id),
                            "collected_by": str(payment.collected_by),
                            "status": str(payment.status),
                            "type": str(payment.type),
                            # "params": payment.params,
                            "params": {
                                "bank_code": "sdfsd",
                                "bank_account_number": "sdfsd",
                                "virtual_payment_address": "sdfsdf",
                            },
                        }
                    ],
                    "cancellation_terms": {
                        "cancel_by": {"duration": "SOMETHING"},
                        # CancellationTerms.objects.get(id = 1).cancel_by,
                        # "cancel_by": {
                        #     "duration": ""
                        # }, # Duration for cancellation of order
                        "cancellation_fee": {"percentage": "SOMETHING"}
                        # CancellationTerms.objects.get(id = 1).cancellation_fee,
                        # "cancellation_fee": {
                        #     "percentage": "",
                        # }
                    }
                }
            }
        }

    def ondc_to_chartr(self, request, *args, **kwargs):
        '''
            format of order:
            {
                "items": [
                    {
                        "id": "I1",
                        "quantity": {
                            "selected": {
                                "count": 2
                            }
                        }
                    }
                ],
                "provider": {
                    "id": "P1"
                },
                "billing": {
                    "name": "John Doe",
                    "email": "john.doe@example.com",
                    "phone": "+91-9897867564"
                },
                "payments": [
                    {
                        "collected_by": "BAP",
                        "status": "NOT-PAID",
                        "type": "PRE-ORDER",
                    }
                ]
            }
        '''
        print(dict(request.GET))
        item = Item.objects.get(id=int(request.GET['order']['items'][0]['id'][1:]))

        billing = Billing.objects.create(
            name=request.GET['order']['billing']['name'],
            email=request.GET['order']['billing']['email'],
            phone=request.GET['order']['billing']['phone']
        )

        payment = Payment.objects.create(
            type=request.GET['order']['payments'][0]['type'],
            status=request.GET['order']['payments'][0]['status'],
            collected_by=request.GET['order']['payments'][0]['collected_by'],
            billing=billing,
            item=item
        )

        return item, billing, payment
