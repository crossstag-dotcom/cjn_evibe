"""Atomic finished-goods receipt into the existing warehouse ledger.

Existing ProductVariant has product_code + size, but no dedicated colour/SKU field.
This service requires an existing variant and never guesses a colour or creates one.
"""
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from apps.store.models import (
    FinishedGoodsReceipt, FinishingBatch, FinishingBatchSize, ProductVariant, StockMovement,
)
from apps.store.services.inventory_service import get_main_warehouse, post_stock_movement


@transaction.atomic
def post_finished_goods_receipt(*, finishing_size_id, variant_id, quantity, reference, user):
    if not user or not user.is_authenticated or not (
        user.has_perm("store.add_finishedgoodsreceipt")
        and user.has_perm("store.add_stockmovement")
    ):
        raise PermissionDenied("Finished-goods receipt and stock-posting permissions are required.")

    reference = str(reference or "").strip()
    if not reference or len(reference) > 100:
        raise ValidationError("Receipt reference must contain 1 to 100 characters.")
    if type(quantity) is not int or quantity <= 0:
        raise ValidationError("Receipt quantity must be a positive integer.")

    # Lock parent to serialize concurrent posting for this finishing batch.
    finishing_size = FinishingBatchSize.objects.select_related("batch").get(pk=finishing_size_id)
    batch = FinishingBatch.objects.select_for_update().get(pk=finishing_size.batch_id)
    finishing_size = FinishingBatchSize.objects.select_for_update().get(pk=finishing_size_id)
    if batch.status != FinishingBatch.Status.COMPLETED:
        raise ValidationError("Finishing must be completed before stock receipt.")
    if finishing_size.finished_pieces is None or quantity != finishing_size.finished_pieces:
        raise ValidationError("Receipt must match the completed quantity for this finishing size.")
    if FinishedGoodsReceipt.objects.filter(finishing_size=finishing_size).exists():
        raise ValidationError("This finishing size was already received into stock.")
    if FinishedGoodsReceipt.objects.filter(reference=reference).exists():
        raise ValidationError("Finished-goods receipt reference already exists.")

    variant = ProductVariant.objects.select_related("product").get(pk=variant_id)
    if variant.size != finishing_size.size:
        raise ValidationError("Product variant size does not match the finished garment size.")
    if not variant.product.active:
        raise ValidationError("Cannot receive finished goods against an inactive product.")
    warehouse = get_main_warehouse()
    # The ledger's duplicate check and balance update run in this same transaction.
    movement = post_stock_movement(
        variant=variant, warehouse=warehouse, delta=quantity,
        reason=StockMovement.Reason.RECEIPT,
        reference=reference, user=user,
    )
    return FinishedGoodsReceipt.objects.create(
        finishing_size=finishing_size, variant=variant, warehouse=warehouse,
        stock_movement=movement, quantity=quantity,
        reference=reference, posted_by=user,
    )
