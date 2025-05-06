from main.models.request import (
    Item,
    Payment,
    Order
)
from main.transformers.base import RequestBodyTransformer


class ConfirmTransformer(RequestBodyTransformer):

    def chartr_to_ondc(self, order, item, billing, fulfilment, payment, *args,
                       context=None, **kwargs):
        # TODO: add authorization field to start stop of fulfilment
        # stops = eval(fulfilment.stops)
        # stops[0]['authorization'] = {
        #     "type":"QR",
        #     "token":"sdfsdf",
        #     "valid_to": "sdfsdf",
        # }
        # print(stops)
        # fulfilment.stops = str(stops)
        # fulfilment.save()

        return {
            "context": context,
            "message": {
                "order": {
                    "id": str(order.id),
                    "items": [
                        {
                            "id": str(item.id),
                            "descriptor": {
                                "name": "asdas",
                                "code": "asdas",
                                "images": [
                                    {
                                        "url": "asdasd"
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
                            "name": "asdasd",
                            "code": "asdasd",
                            "images": [
                                {
                                    "url": "asdasd"
                                }
                            ]
                        },
                    },
                    "fulfillments": {
                        "stops": eval(fulfilment.stops),
                        "vehicle": eval(fulfilment.vehicle),
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
                                "transaction_id": "asdasd",
                                "currency": "INR",
                                "amount": "89",
                                "bank_code": "asdasd",
                                "bank_account_number": "asdasd",
                                "virtual_payment_address": "asdasd",
                            },
                        }
                    ],
                    "cancellation_terms": {
                        # "cancel_by": CancellationTerms.objects.get(id = 1).cancel_by,
                        "cancel_by": {
                            "duration": "asdasd"
                        },  # Duration for cancellation of order
                        # "cancellation_fee": CancellationTerms.objects.get(id = 1).cancellation_fee,
                        "cancellation_fee": {
                            "percentage": "asdasd",
                        }
                    }
                }
            }
        }

    def ondc_to_chartr(self, request, *args, **kwargs):
        '''
            format of order:
            {
                "id": "O1",
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
                        "id": "P1",
                        "collected_by": "BAP",
                        "status": "NOT-PAID",
                        "type": "PRE-ORDER",
                    }
                ]
            }
        '''
        item = Item.objects.get(id=int(request.GET['order']['items'][0]['id'][1:]))
        # print(request.GET['order']['payments'])
        payment = Payment.objects.get(
            id=int(request.GET['order']['payments'][0]['id'][2:]))

        order, _ = Order.objects.get_or_create(
            items=item,
            billing=payment.billing,
            payments=payment,
            # cancellation_terms = CancellationTerms.objects.get(id = 1)
        )

        billing = payment.billing

        fulfilment = item.fulfillment

        return order, item, billing, fulfilment, payment
