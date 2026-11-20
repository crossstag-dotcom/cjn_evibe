"""Warehouse-level stock ledger. Schema requires a Django migration before use."""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class Warehouse(models.Model):
    code = models.CharField(max_length=24, unique=True)
    name = models.CharField(max_length=120)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class InventoryBalance(models.Model):
    variant = models.ForeignKey("store.ProductVariant", on_delete=models.PROTECT, related_name="warehouse_balances")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name="balances")
    quantity = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["variant", "warehouse"], name="unique_variant_warehouse_balance"),
        ]


class StockMovement(models.Model):
    class Reason(models.TextChoices):
        RECEIPT = "RECEIPT", "Goods receipt"
        ISSUE = "ISSUE", "Goods issue"
        RETURN = "RETURN", "Goods return"
        ADJUSTMENT = "ADJUSTMENT", "Authorized adjustment"
        TRANSFER = "TRANSFER", "Warehouse transfer"

    variant = models.ForeignKey("store.ProductVariant", on_delete=models.PROTECT, related_name="stock_movements")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name="movements")
    quantity_delta = models.IntegerField()
    reason = models.CharField(max_length=20, choices=Reason.choices)
    reference = models.CharField(max_length=100)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=~Q(quantity_delta=0), name="stock_movement_nonzero"),
        ]

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError("Stock movements are immutable; post a correction instead.")
        super().save(*args, **kwargs)
