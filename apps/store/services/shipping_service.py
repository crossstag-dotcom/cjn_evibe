import requests
from django.conf import settings

SHIPROCKET_BASE = "https://apiv2.shiprocket.in/v1/external"


def get_shiprocket_token():

    url = f"{SHIPROCKET_BASE}/auth/login"

    data = {
        "email": settings.SHIPROCKET_EMAIL,
        "password": settings.SHIPROCKET_PASSWORD
    }

    response = requests.post(url, json=data)

    return response.json()["token"]


def build_items(order):

    items = []

    for item in order.items.all():
        items.append({
            "name": item.product.name,
            "sku": item.variant.size,
            "units": item.quantity,
            "selling_price": float(item.price)
        })

    return items


def create_shipment(order):

    # MOCK SHIPPING (NO API CALL)

    return {
        "shipment_id": f"SHIP_{order.id}",
        "awb_code": f"AWB_{order.id}",
        "courier_name": "MockCourier"
    }

"""
def create_shipment(order):


    token = get_shiprocket_token()

    payload = {
        "order_id": str(order.id),
        "order_date": order.created_at.strftime("%Y-%m-%d"),
        "pickup_location": "primary",

        "billing_customer_name": order.customer_name,
        "billing_phone": order.phone,
        "billing_address": order.address,
        "billing_city": order.city,
        "billing_pincode": order.pincode,
        "billing_country": "India",

        "payment_method": order.payment_method,

        "order_items": build_items(order),

        "sub_total": float(order.total_amount),
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        f"{SHIPROCKET_BASE}/orders/create/adhoc",
        json=payload,
        headers=headers
    )

    return response.json()
"""