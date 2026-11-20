from django.shortcuts import render, get_object_or_404, redirect
from apps.store.models import Order, ReturnRequest
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from apps.store.services.configuration_service import get_store_config

def my_orders(request):

    customer_email = request.session.get(
        "evibe_customer_email"
    )

    if not customer_email:

        return redirect(
            "order_access"
        )

    orders = (Order.objects.filter(
            email=customer_email
        )
        .select_related("invoice")
        .order_by(
            "-created_at"
        )
    )

    return render(
        request,
        "store/my_orders.html",
        {
            "orders": orders
        }
    )

def track_order(
    request,
    order_id
):

    customer_email = request.session.get(
        "evibe_customer_email"
    )

    if not customer_email:

        return redirect(
            "order_access"
        )

    order = get_object_or_404(
        Order,
        id=order_id,
        email=customer_email
    )

    return render(
        request,
        "store/track_order.html",
        {
            "order": order
        }
    )

def order_access(request):

    customer_email = request.session.get(
        "evibe_customer_email"
    )

    if customer_email:

        return redirect(
            "my_orders"
        )

    return render(
        request,
        "store/order_access.html"
    )



# For simplicity, we assume one item per order in this example
def request_return(request, order_id):

    customer_email = request.session.get(
        "evibe_customer_email"
    )

    if not customer_email:

        return redirect(
            "order_access"
        )

    order = get_object_or_404(
        Order,
        id=order_id,
        email=customer_email
    )

    if not order.exchange_allowed:

        messages.error(
            request,
            "This order is not eligible for returns or exchanges."
        )

        return redirect(
            "track_order",
            order.id
        )
    
    if not order.delivered_at:

        messages.error(
            request,
            "Delivery Date missing."
        )

        return redirect(
            "track_order",
            order.id
        )

    # Must be delivered
    if order.status != "DELIVERED":

        messages.error(
            request,
            "Return allowed only after delivery."
        )

        return redirect(
            "track_order",
            order.id
        )

    # 5-day window


    config = get_store_config()

    return_deadline = (
        order.delivered_at +
        timedelta(days=config.return_window_days)
    )
    if timezone.now() > return_deadline:

        messages.error(
            request,
            "Return window expired."
        )

        return redirect(
            "track_order",
            order.id
        )

    if request.method == "POST":

        order_item = order.items.first()

        ReturnRequest.objects.create(

            order=order,

            order_item=order_item,

            quantity=1,

            reason=request.POST.get(
                "reason"
            ),

            customer_comments=request.POST.get(
                "customer_comments"
            ),

            preferred_pickup_date=request.POST.get(
                "preferred_pickup_date"
            )

        )

        messages.success(
            request,
            "Return request submitted successfully."
        )

        return redirect(
            "track_order",
            order.id
        )

    return render(
        request,
        "store/request_return.html",
        {
            "order": order
        }
    )