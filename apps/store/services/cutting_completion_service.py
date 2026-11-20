"""Finalize cutting actuals atomically while preserving leftovers in cutting."""
from decimal import Decimal, InvalidOperation

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from apps.store.models import (
    CuttingCompletion, CuttingCompletionSize, CuttingOrder, FabricRoll,
)


def _meters(value, label):
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValidationError(f"{label} must be numeric.") from None
    if not amount.is_finite() or amount < 0 or amount.as_tuple().exponent < -3:
        raise ValidationError(f"{label} must be nonnegative with at most 3 decimals.")
    return amount


@transaction.atomic
def complete_cutting(*, cutting_order_id, actual_sizes, consumed_meters, waste_meters, user):
    """Post actual output once; reduce roll balance only by consumed + waste.

    The unused remainder stays assigned to the cutting department.
    """
    if not user or not user.is_authenticated or not user.has_perm("store.change_cuttingorder"):
        raise PermissionDenied("Not authorized to complete cutting.")

    order = CuttingOrder.objects.select_for_update().get(pk=cutting_order_id)
    roll = FabricRoll.objects.select_for_update().get(pk=order.roll_id)

    if order.status != CuttingOrder.Status.ISSUED or roll.location != FabricRoll.Location.CUTTING:
        raise ValidationError("Only issued cutting orders with a roll in cutting can be completed.")
    if CuttingCompletion.objects.filter(order=order).exists():
        raise ValidationError("This cutting order already has a completion.")

    planned_sizes = set(order.size_lines.values_list("size", flat=True))
    if not isinstance(actual_sizes, dict) or set(actual_sizes) != planned_sizes:
        raise ValidationError("Provide actual pieces for every planned size.")
    if any(type(pieces) is not int or pieces < 0 for pieces in actual_sizes.values()):
        raise ValidationError("Actual pieces must be nonnegative whole numbers.")

    consumed = _meters(consumed_meters, "Consumed meters")
    waste = _meters(waste_meters, "Waste meters")
    if consumed + waste > roll.available_meters:
        raise ValidationError("Consumed and waste meters exceed available fabric.")
    if consumed == 0 and waste == 0 and not any(actual_sizes.values()):
        raise ValidationError("An empty completion cannot be posted.")

    leftover = roll.available_meters - consumed - waste
    completion = CuttingCompletion.objects.create(
        order=order, consumed_meters=consumed, waste_meters=waste,
        leftover_meters=leftover, completed_by=user,
    )
    CuttingCompletionSize.objects.bulk_create([
        CuttingCompletionSize(completion=completion, size=size, actual_pieces=pieces)
        for size, pieces in actual_sizes.items()
    ])
    roll.available_meters = leftover
    roll.save(update_fields=["available_meters"])
    order.status = CuttingOrder.Status.COMPLETED
    order.save(update_fields=["status"])
    return completion
