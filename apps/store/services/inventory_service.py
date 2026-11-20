from django.db import transaction
from ..models import ProductVariant

# -----------------------
# FULL STOCK RESTORE (CANCELLED)
# -----------------------
def restore_full_stock(order):

        for item in order.items.select_related('variant'):

            variant = ProductVariant.objects.select_for_update().get(
                id=item.variant.id
            )

            variant.stock += item.quantity
            variant.save()


# -----------------------
# PARTIAL STOCK RESTORE (RETURN)
# -----------------------
def restore_partial_stock(order):

        for item in order.items.select_related('variant'):

            qty = item.returned_quantity

            if qty > 0:

                variant = ProductVariant.objects.select_for_update().get(
                    id=item.variant.id
                )

                variant.stock += qty
                variant.save()

# Warehouse ledger V1. Legacy order stock restoration above remains unchanged.
from django.core.exceptions import ValidationError
from django.db.models import F
from apps.store.models.inventory import InventoryBalance, StockMovement, Warehouse


@transaction.atomic
def post_stock_movement(*, variant, warehouse, delta, reason, reference, user):
    """Post a warehouse movement atomically; does not modify legacy variant.stock."""
    if not user or not user.is_authenticated or not user.has_perm("store.add_stockmovement"):
        raise ValidationError("Not authorized to post inventory movements.")
    if not isinstance(delta, int) or isinstance(delta, bool) or delta == 0:
        raise ValidationError("Quantity delta must be a non-zero integer.")
    if not reference or not reference.strip():
        raise ValidationError("A reference is required.")
    if reason not in StockMovement.Reason.values:
        raise ValidationError("Invalid stock movement reason.")
    # Lock warehouse before checking references and creating balances.
    locked_warehouse = Warehouse.objects.select_for_update().get(pk=warehouse.pk)
    if not locked_warehouse.active:
        raise ValidationError("Warehouse is inactive.")
    if StockMovement.objects.filter(
        variant=variant, warehouse=warehouse, reason=reason, reference=reference
    ).exists():
        raise ValidationError("Duplicate movement reference.")
    balance, _ = InventoryBalance.objects.get_or_create(
        variant=variant, warehouse=warehouse, defaults={"quantity": 0}
    )
    balance = InventoryBalance.objects.select_for_update().get(pk=balance.pk)
    if balance.quantity + delta < 0:
        raise ValidationError("Insufficient warehouse stock.")
    InventoryBalance.objects.filter(pk=balance.pk).update(quantity=F("quantity") + delta)
    return StockMovement.objects.create(
        variant=variant, warehouse=warehouse, quantity_delta=delta,
        reason=reason, reference=reference, created_by=user
    )


@transaction.atomic
def transfer_stock(*, variant, source, destination, quantity, reference, user):
    if source.pk == destination.pk:
        raise ValidationError("Source and destination must differ.")
    if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity <= 0:
        raise ValidationError("Transfer quantity must be positive.")
    list(Warehouse.objects.select_for_update().filter(
        pk__in=[source.pk, destination.pk]
    ).order_by("pk"))
    outgoing = post_stock_movement(
        variant=variant, warehouse=source, delta=-quantity,
        reason=StockMovement.Reason.TRANSFER, reference=reference, user=user
    )
    incoming = post_stock_movement(
        variant=variant, warehouse=destination, delta=quantity,
        reason=StockMovement.Reason.TRANSFER, reference=reference, user=user
    )
    return outgoing, incoming


# Single-warehouse configuration for EVIBE/DENVIX finished goods.
MAIN_WAREHOUSE_CODE = "MAIN"


def get_main_warehouse():
    """Return the configured main warehouse; do not silently create live stock locations."""
    try:
        return Warehouse.objects.get(code=MAIN_WAREHOUSE_CODE, active=True)
    except Warehouse.DoesNotExist as exc:
        raise ValidationError(
            "Main Warehouse is not configured. Create warehouse code MAIN before posting stock."
        ) from exc


def post_main_warehouse_movement(*, variant, delta, reason, reference, user):
    """Post finished-goods movement to the single operating warehouse."""
    return post_stock_movement(
        variant=variant, warehouse=get_main_warehouse(), delta=delta,
        reason=reason, reference=reference, user=user
    )
