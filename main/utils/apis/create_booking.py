import sqlite3

import requests

from main.utils.apis import BASE_URL


def create_booking(order, item):
    conn = sqlite3.connect('../../../updated_db.sqlite3')
    cur = conn.cursor()

    fulfilment = item.fulfilment

    cur.execute(f'''
            SELECT * FROM stops
            WHERE stop_name in [
                    {fulfilment.stops[0]['location']['code']}, 
                    {fulfilment.stops[-1]['location']['code']}
                ]
            order by stop_pos
            ''')
    stops = cur.fetchall()
    start_stop = stops[0]
    end_stop = stops[1]

    conn.close()
    booking_json = {
        "data":
            {
                "api_version": 3,
                "vendor_booking_id": str(order.id),
                "route": "970UP",
                "bus_registration_number": None,
                "user_start_stop_index": start_stop[2],
                "user_end_stop_index": end_stop[2],
                "category": "G",
                "ticket_count": int(item.quantity),
            },
        "db_version": 99
    }
    response = requests.post(BASE_URL + 'api/otp/v4/booking/', json=booking_json)
    print("CREATE BOOKING ", response.json())
