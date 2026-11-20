"""Auditable finished-goods receipt per finishing size and product variant."""
from django.conf import settings
from django.db import models
from django.db.models import Q


class FinishedGoodsReceipt(models.Model):
    finishing_size = models.OneToOneField(
        "store.FinishingBatchSize", on_delete=models.PROTECT, related_name="goods_receipt"
    )
    variant = models.ForeignKey(
        "store.ProductVariant", on_delete=models.PROTECT, related_name="manufacturing_receipts"
    )
    warehouse = models.ForeignKey(
        "store.Warehouse", on_delete=models.PROTECT, related_name="manufacturing_receipts"
    )
    stock_movement = models.OneToOneField(
        "store.StockMovement", on_delete=models.PROTECT, related_name="finished_goods_receipt"
    )
    quantity = models.PositiveIntegerField()
    reference = models.CharField(max_length=100, unique=True)
    posted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="finished_goods_receipts"
    )
    posted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(quantity__gt=0), name="fg_receipt_quantity_positive"),
        ]
