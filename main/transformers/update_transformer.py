from main.models.request import Order, CancellationTerms, Billing
from main.transformers.base import RequestBodyTransformer


class UpdateTransformer(RequestBodyTransformer):

    def chartr_to_ondc(self, order, item, fulfilment, billing, payment, *args,
                       **kwargs):
        return {
            "context": {
                "action": "on_update",
                # rest of the fields on_update_request.body['context]
            },
            "message": {
                "order": {
                    "id": str(order.id),
                    "items": [
                        {
                            "id": str(item.id),
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
                            "name": "",
                            "images": [
                                {
                                    "url": ""
                                }
                            ]
                        },
                    },
                    "fulfillments": {
                        "stops": fulfilment.stops,
                        "vehicle": fulfilment.vehicle,
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
                    "payements": [
                        {
                            "id": str(payment.id),
                            "collected_by": str(payment.collected_by),
                            "status": str(payment.status),
                            "type": str(payment.type),
                            "params": payment.params,
                            # "params": {
                            #     "transaction_id": "",
                            #     "currency": "INR",
                            #     "amount": "",
                            #     "bank_code": "",
                            #     "bank_account_number": "",
                            #     "virtual_payment_address": "",
                            # },
                        }
                    ],
                    "cancellation_terms": {
                        "cancel_by": CancellationTerms.objects.get(id=1).cancel_by,
                        # "cancel_by": {
                        #     "duration": ""
                        # }, # Duration for cancellation of order
                        "cancellation_fee": CancellationTerms.objects.get(
                            id=1).cancellation_fee,
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
                "id": "O1",
                "billing": {
                    "name": "John Doe",
                    "email": "",
                    "phone": "",
                },
            }
        '''
        order = Order.objects.get(id=int(request['order']['id']))
        # update_target = request['update_target']

        Billing.object.filter(id=order.billing).update(**request['order']['billing'])

        # order, item, fulfilment, billing, payment,
        return order, order.item, order.item.fulfillment, order.billing, order.payments
