import requests

from main.utils.apis import BASE_URL


def confirm_booking(order):
    response = requests.post(
        f'{BASE_URL}api/otp/v3/booking/confirm?vendor_booking_id={order.id}'
    )
    print("CONFIRM BOOKING", response.json())
