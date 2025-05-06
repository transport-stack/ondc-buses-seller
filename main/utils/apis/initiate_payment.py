import requests

from main.utils.apis import BASE_URL


def initiate_payment(order):
    response = requests.post(
        f'{BASE_URL}/api/otp/v3/initiate-transaction/',
        data={
            "data": {
                "vendor_booking_id": f"{order.id}",
                "pg": 0,
                "payment_mode": None,
                "payment_flow": 0,
                "transaction_type": 1
            }
        }
    )
    print("INITIATE PAYMENT", response.json())
