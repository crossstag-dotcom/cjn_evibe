from django.db import models, transaction
from django.db.models import Sum
from django.core.exceptions import ValidationError
from datetime import timedelta
from django.utils import timezone

from .order import OrderItem
from .refund import Refund
from ..services.configuration_service import get_store_config

#   The ReturnRequest model manages product return requests, linking to the Order and specific OrderItem. It tracks the quantity being returned, the status of the return process, and any inspection notes. The save method includes validation to ensure that return quantities do not exceed what was ordered and that status transitions follow a defined workflow. When a return is approved, it updates the returned quantity on the OrderItem and triggers an order status update to reflect the return process.
class ReturnRequest(models.Model):

    STATUS_CHOICES = [
        ('REQUESTED', 'Requested'),
        ('APPROVED', 'Approved'),
        ('PICKUP_SCHEDULED', 'Pickup Scheduled'),
        ('PICKED', 'Picked'),
        ('RECEIVED', 'Received'),

        ('QC_APPROVED', 'QC Approved'),
        ('QC_REJECTED', 'QC Rejected'),

        ('REJECTED', 'Rejected'),
    ]

    RETURN_REASONS = [

        ("SIZE", "Size Issue"),

        ("FIT", "Fit Issue"),

        ("WRONG_PRODUCT", "Wrong Product"),

        ("DAMAGED", "Damaged Product"),

        ("QUALITY", "Quality Issue"),

        ("OTHER", "Other"),
    ]

    order = models.ForeignKey("Order", on_delete=models.CASCADE)
    order_item = models.ForeignKey("OrderItem", on_delete=models.CASCADE)

    quantity = models.PositiveIntegerField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='REQUESTED'
    )

    inspection_notes = models.TextField(blank=True, null=True)

    reason = models.CharField(max_length=30, choices=RETURN_REASONS, blank=True, null=True)

    customer_comments = models.TextField(blank=True, null=True)

    preferred_pickup_date = models.DateField(blank=True, null=True)

    refund_processed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    processed_at = models.DateTimeField(blank=True, null=True)


    def save(self, *args, **kwargs):

        from ..services.return_service import update_return_status 
        from ..services.timeline_service  import log_order_event
        from ..models import Refund, OrderItem

        with transaction.atomic():

            is_new = self.pk is None

            # -----------------------------
            # BASIC VALIDATION
            # -----------------------------
            if self.quantity <= 0:
                raise ValidationError("Return quantity must be greater than zero")

            if self.quantity > self.order_item.quantity:
                raise ValidationError("Return qty cannot exceed ordered qty")

            # -----------------------------
            # RETURN WINDOW VALIDATION
            # -----------------------------
            if not self.order.delivered_at:
                raise ValidationError("Return allowed only after delivery")


            config = get_store_config()

            return_deadline = (
                self.order.delivered_at +
                timedelta(days=config.return_window_days)
            )

            if timezone.now() > return_deadline:
                raise ValidationError("Return window closed (5 days)")

            # -----------------------------
            # CUMULATIVE RETURN VALIDATION
            # -----------------------------
            existing_qty = ReturnRequest.objects.filter(
                order_item=self.order_item
            ).exclude(pk=self.pk).aggregate(
                total=Sum("quantity")
            )["total"] or 0

            if existing_qty + self.quantity > self.order_item.quantity:

                remaining = self.order_item.quantity - existing_qty

                raise ValidationError(
                    f"Return exceeds ordered quantity. Remaining allowed: {remaining}"
                )

            # -----------------------------
            # STATUS TRANSITION VALIDATION
            # -----------------------------
            old_status = None

            if self.pk is not None:

                old = ReturnRequest.objects.select_for_update().get(pk=self.pk)

                old_status = old.status

                allowed_transitions = {
                    "REQUESTED": ["APPROVED", "REJECTED"],
                    "APPROVED": ["PICKED"],
                    "PICKUP_SCHEDULED": ["PICKED"],
                    "PICKED": ["RECEIVED"],
                    "RECEIVED": ["QC_APPROVED", "QC_REJECTED"],
                    "QC_APPROVED": [],
                    "QC_REJECTED": [],
                    "REJECTED": []
                }

                if self.status != old.status:

                    if self.status not in allowed_transitions.get(old.status, []):

                        raise ValidationError(
                            f"Invalid transition: {old.status} → {self.status}"
                        )

            # -----------------------------
            # QC APPROVED FLOW
            # -----------------------------
            if (old_status != "QC_APPROVED") and self.status == "QC_APPROVED":

                order_item = OrderItem.objects.select_for_update().get(
                    id=self.order_item.id
                )

                if order_item.returned_quantity + self.quantity > order_item.quantity:

                    raise ValidationError(
                        "Total returned exceeds ordered quantity"
                    )

                # update returned quantity
                order_item.returned_quantity += self.quantity
                order_item.save()

                # update order return status
                update_return_status(self.order)

                # -----------------------------
                # AUTO CREATE REFUND RECORD
                # -----------------------------
                refund_amount = self.quantity * order_item.price

                existing = Refund.objects.filter(
                    order=self.order,
                    status="INITIATED",
                    amount=refund_amount
                ).exists()

                if not existing:

                    Refund.objects.create(
                        order=self.order,
                        amount=refund_amount,
                        status="INITIATED"
                    )

                self.processed_at = timezone.now()

                # -----------------------------
                # TIMELINE LOG
                # -----------------------------
                log_order_event(
                    self.order,
                    "RETURN",
                    f"{self.quantity} item(s) returned for {order_item.product.name}"
                )

            super().save(*args, **kwargs)

            # -----------------------------
            # MARK RETURN IN PROGRESS
            # -----------------------------
            if is_new:

                self.order.return_status = "IN_PROGRESS"
                self.order.save()


    def __str__(self):

        return f"Return #{self.id} | Order {self.order.id} | Qty {self.quantity} | {self.status}" 