import sqlite3

from main.config import Config
from main.models.request import Item
from main.transformers.base import RequestBodyTransformer


class SelectTransformer(RequestBodyTransformer):

    def chartr_to_ondc(self, item, fulfilment, *args, context=None, **kwargs):
        return {
            "context": context,
            "message": {
                "order": {
                    "items": [
                        {
                            "id": str(item.id),
                            "descriptor": {
                                "name": "asda",
                                "code": "sdfvdf",
                                "images": [
                                    {
                                        "url": "dfdfgfg"
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
                                str(fulfilment.id)
                            ]
                        }
                    ],
                    "provider": {
                        "id": "P1",
                        "descriptor": {
                            "name": "dfgdf",
                            "code": "dfgdf",
                            "images": [
                                {
                                    "url": "dfgdfg"
                                }
                            ]
                        },
                    },
                    "fulfillments": [
                        {
                            "id": str(fulfilment.id),
                            "stops": eval(fulfilment.stops),
                            "vehicle": eval(fulfilment.vehicle),
                        }
                    ],
                    "quote": {
                        "price": {
                            "value": str(item.price),
                            "currency": "INR"
                        },
                        "breakup": [
                            {
                                "title": "Base Fare",
                                "item": {
                                    "id": str(item.id),
                                },
                                "price": {
                                    "currency": "INR",
                                    "value": str(item.price)
                                }
                            }
                        ]
                    }
                }
            }
        }

    def ondc_to_chartr(self, request, *args, **kwargs):
        conn = sqlite3.connect(Config.CHARTR_DB)
        cur = conn.cursor()

        '''
        [
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
                }, # item['quantity'],
                "fulfillment_ids": [
                    "F1"
                ]
            }
            for item in items
        ],
        '''
        item = Item.objects.get(id=int(request.GET['items'][0]['id'][1:]))

        item.quantity = request.GET['items'][0]['quantity']['selected']['count']

        fulfilment = item.fulfillment
        stops = eval(fulfilment.stops)

        cur.execute(f'''
            SELECT * FROM stops
            WHERE stop_name in (
                    '{stops[0]['location']['descriptor']['code']}', 
                    '{stops[-1]['location']['descriptor']['code']}'
                )
            order by stop_pos
            ''')
        stops = cur.fetchall()

        start_stop = stops[0]
        end_stop = stops[1]

        # TODO: Get Route
        cur.execute(f'''
            SELECT * FROM all_routes
            WHERE route_long_name = '{start_stop[1]}'
            and is_ac = {start_stop[0].split('_')[-1]}
                    ''')
        route = cur.fetchone()
        fare_matrix = eval(route[5])  # Fare Matrix

        # TODO: Calculate Price
        item.price = item.quantity * fare_matrix[str(start_stop[2])][str(end_stop[2])][
            "basic_fare"]

        item.save()
        print(item.price)

        return item, fulfilment
