"""Read-only comparison of storefront stock and existing warehouse ledger.

No stock is changed; do not auto-sync until order deductions and returns are ledger-backed.
"""
from django.core.exceptions import ValidationError
from django.db.models import Sum

from apps.store.models import InventoryBalance, ProductVariant, Warehouse


def get_variant_stock_reconciliation(*, variant_id):
    variant = ProductVariant.objects.select_related("product").get(pk=variant_id)
    main = Warehouse.objects.filter(code="MAIN", active=True).first()
    if main is None:
        raise ValidationError("Active MAIN warehouse is not configured.")
    ledger_quantity = (
        InventoryBalance.objects.filter(variant=variant, warehouse=main)
        .aggregate(total=Sum("quantity"))["total"] or 0
    )
    identity = getattr(variant, "identity", None)
    return {
        "variant_id": variant.pk,
        "article_code": variant.product.product_code,
        "size": variant.size,
        "sku": identity.sku if identity else None,
        "colour": identity.colour if identity else None,
        "warehouse": main.code,
        "warehouse_quantity": ledger_quantity,
        "storefront_quantity": variant.stock,
        "difference": ledger_quantity - variant.stock,
        "in_sync": ledger_quantity == variant.stock,
        "sync_mode": "READ_ONLY",
        "automatic_sync_enabled": False,
    }
