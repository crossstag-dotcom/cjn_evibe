import json
import razorpay

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.core.mail import send_mail

from apps.store.core.cart_manager import Cart
from apps.store.models import Order
from apps.store.services.order_service import update_order_status


# -----------------------------------------
# PAYMENT SUCCESS (Razorpay redirect)
# -----------------------------------------
@csrf_exempt
def payment_success(request):

    if request.method == "POST":

        razorpay_order_id = request.POST.get("razorpay_order_id")
        razorpay_payment_id = request.POST.get("razorpay_payment_id")
        razorpay_signature = request.POST.get("razorpay_signature")

        try:

            order = get_object_or_404(
                Order,
                razorpay_order_id=razorpay_order_id
            )

            client = razorpay.Client(
                auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
            )

            # Verify signature
            client.utility.verify_payment_signature({
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": razorpay_signature
            })

            # Idempotent check
            if order.status == "CREATED":

                order.razorpay_payment_id = razorpay_payment_id
                order.razorpay_signature = razorpay_signature

                if order.payment_method == "ONLINE":
                    order.payment_status = "PAID"
                else:
                    order.payment_status = "PARTIALLY_PAID"

                order.save()

                update_order_status(order, "PAID")

                # Send email confirmation
                if order.email:

                    send_mail(
                        subject=f"EVIBE Order #{order.id} Confirmed",
                        message=f"""
Hi {order.customer_name},

Thank you for shopping with EVIBE.

Your order has been placed successfully.

Order ID: {order.id}
Total Amount: ₹{order.total_amount}

We will notify you once your order is shipped.

Thanks,
EVIBE Team
""",
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[order.email],
                        fail_silently=True,
                    )

            # Clear cart
            cart = Cart(request)
            cart.clear()

            return redirect("/order-success/")

        except razorpay.errors.SignatureVerificationError:

            if 'order' in locals():
                order.status = "CANCELLED"
                order.save()

            return render(request, "store/payment_failed.html")

    return redirect("/")


# -----------------------------------------
# RAZORPAY WEBHOOK
# -----------------------------------------
@csrf_exempt
def razorpay_webhook(request):

    webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET

    payload = request.body
    signature = request.headers.get("X-Razorpay-Signature")

    client = razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )

    try:

        client.utility.verify_webhook_signature(
            payload,
            signature,
            webhook_secret
        )

        data = json.loads(payload)

        if data["event"] == "payment.captured":

            payment = data["payload"]["payment"]["entity"]

            razorpay_order_id = payment["order_id"]
            razorpay_payment_id = payment["id"]

            try:
                order = Order.objects.get(
                    razorpay_order_id=razorpay_order_id
                )
            except Order.DoesNotExist:
                return HttpResponse(status=200)

            with transaction.atomic():

                if order.status != "PAID":

                    order.razorpay_payment_id = razorpay_payment_id

                    if order.payment_method == "ONLINE":
                        order.payment_status = "PAID"
                    else:
                        order.payment_status = "PARTIALLY_PAID"

                    order.save()

                    update_order_status(order, "PAID")

        return HttpResponse(status=200)

    except Exception as e:

        print("Webhook error:", e)

        return HttpResponse(status=400)


# -----------------------------------------
# COURIER WEBHOOK
# -----------------------------------------
@csrf_exempt
def courier_webhook(request):

    data = json.loads(request.body)

    awb = data.get("awb")
    status = data.get("status")

    try:

        order = Order.objects.get(awb_code=awb)

        update_order_status(order, status)

    except Order.DoesNotExist:
        pass

    return HttpResponse(status=200)