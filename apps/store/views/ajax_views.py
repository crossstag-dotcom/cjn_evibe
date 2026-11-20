import re
from django.http import JsonResponse
from apps.store.models import OrderItem
from apps.store.services.pincode_service import (
    get_location_from_pincode
)


def get_order_items(request):

    order_id = request.GET.get("order_id")

    items = OrderItem.objects.filter(order_id=order_id)

    data = [
        {
            "id": item.id,
            "text": f"{item.product.name} (Qty: {item.quantity})"
        }
        for item in items
    ]

    return JsonResponse({"items": data})


def get_pincode_details(request):

    result = get_location_from_pincode(
        request.GET.get("pincode", "")
    )

    if not result.success:
        return JsonResponse({
            "success": False,
            "message": result.message
        })

    return JsonResponse({
        "success": True,
        "pincode": result.pincode,
        "city": result.city,
        "district": result.district,
        "state": result.state,
    })
