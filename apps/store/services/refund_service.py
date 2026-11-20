from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
import razorpay

from django.conf import settings

from ..models import Order, Refund, ReturnRequest


# -----------------------
# CALCULATE REFUND
# -----------------------
def calculate_refund_amount(order):

    # RTO → full refund
    if order.status == "RTO":
        return order.total_amount

    # Customer return → partial refund
    total = 0

    for item in order.items.all():
        refundable_qty = item.returned_quantity - item.refunded_quantity

        if refundable_qty > 0:
            total += refundable_qty * item.price

    return total


# ----------------------- 
#   Process refund via Razorpay.
#
#    Supports:
#    - RTO full refund
#    - Customer partial return refund
#    - Idempotency (prevents duplicate refunds)
#    - Admin-controlled refund execution
#
#    Parameters:
#    - order: Order object
#    - refund_obj: existing Refund object (from admin), optional
#
#    Returns:
#    - refund object (updated)
# -----------------------
@transaction.atomic
def process_refund(order, refund, return_request=None):
    """
    Unified refund handler

    Supports:
    1. Customer return refund (via ReturnRequest)
    2. RTO refund (no ReturnRequest)

    Fully idempotent + concurrency safe
    """

    # 🔒 Lock order (important for RTO + concurrency)
    order = Order.objects.select_for_update().get(id=order.id)

    # 🔒 Lock refund row (prevents double execution)
    refund = Refund.objects.select_for_update().get(id=refund.id)

    # -----------------------------
    # COMMON VALIDATIONS
    # -----------------------------
    if order.payment_method != "ONLINE":
        raise ValidationError("Refund only allowed for ONLINE payments")

    if not order.razorpay_payment_id:
        raise ValidationError("Missing Razorpay payment ID")

    refund_amount = 0
    items_to_update = []

    # =========================================================
    # 🟢 CASE 1: CUSTOMER RETURN FLOW
    # =========================================================
    if return_request:

        return_request = ReturnRequest.objects.select_for_update().select_related(
            "order_item"
        ).get(id=return_request.id)

        if return_request.status != "QC_APPROVED":
            raise ValidationError("Refund allowed only after QC_APPROVED")

        if return_request.refund_processed:
            raise ValidationError("Refund already processed for this return")

        order_item = return_request.order_item
        refundable_qty = return_request.quantity

        if order_item.refunded_quantity + refundable_qty > order_item.returned_quantity:
            raise ValidationError("Refund exceeds returned quantity")

        if refundable_qty <= 0:
            raise ValidationError("Invalid refund quantity")

        refund_amount = refundable_qty * order_item.price

        items_to_update.append((order_item, refundable_qty))

    # =========================================================
    # 🔵 CASE 2: RTO FLOW
    # =========================================================
    elif order.status == "RTO":
        if not order.stock_restored:
            raise ValidationError("Stock not restored yet for RTO")

        # Prevent duplicate RTO refund
        existing_success = Refund.objects.filter(
            order=order,
            status="SUCCESS"
        ).exists()

        if existing_success:
            raise ValidationError("RTO refund already processed")

        for item in order.items.all():
            refundable_qty = item.quantity - item.refunded_quantity

            if refundable_qty > 0:
                refund_amount += refundable_qty * item.price
                items_to_update.append((item, refundable_qty))

        if refund_amount <= 0:
            raise ValidationError("Nothing left to refund")
        

    else:
        # Customer return refund without specific return_request
        for item in order.items.all():

            refundable_qty = item.returned_quantity - item.refunded_quantity

            if refundable_qty > 0:
                refund_amount += refundable_qty * item.price
                items_to_update.append((item, refundable_qty))

        if refund_amount <= 0:
            raise ValidationError("Nothing left to refund")

    # -----------------------------
    # FINAL AMOUNT CHECK
    # -----------------------------
    if refund_amount <= 0:
        raise ValidationError("Refund amount is zero")

    # -----------------------------
    # CREATE REFUND RECORD
    # -----------------------------
    if refund.status not in ["INITIATED", "FAILED"]:
        raise ValidationError("Refund already processed")
    
    

    total_refunded = Refund.objects.filter(
        order=order,
        status="SUCCESS"
    ).aggregate(
        total=Sum("amount")
    )["total"] or 0

    if total_refunded + refund_amount > order.total_amount:
        raise ValidationError("Refund exceeds order value")
    
    client = razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )

    try:
        # 🔑 Idempotency key
        if return_request:
            receipt = f"refund_rr_{return_request.id}"
        else:
            receipt = f"refund_order_{order.id}_{refund.id}"

        response = client.payment.refund(
            order.razorpay_payment_id,
            {
                "amount": int(refund_amount * 100),
                "receipt": receipt
            }
        )

        # -----------------------------
        # SUCCESS FLOW
        # -----------------------------
        refund.razorpay_refund_id = response.get("id")
        refund.status = "SUCCESS"
        refund.refunded_at = timezone.now()
        refund.save()

        # Update items
        for item, qty in items_to_update:
            item.refunded_quantity += qty
            item.save()

        # Mark return processed
        if return_request:
            return_request.refund_processed = True
            return_request.save()

        return refund

    except Exception as e:
        # -----------------------------
        # FAILURE FLOW
        # -----------------------------
        refund.status = "FAILED"
        refund.save()

        raise ValidationError(f"Refund failed: {str(e)}")