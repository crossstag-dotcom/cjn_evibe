"""Atomic issue of a verified, complete fabric roll to the cutting department."""
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from apps.store.models import CuttingOrder, FabricRoll


@transaction.atomic
def issue_complete_roll_to_cutting(*, cutting_order_id, user):
    """Transfer departmental custody; do not reduce remaining meters.

    The caller must hold the store.change_cuttingorder permission.
    Row locks serialize competing issue attempts on databases supporting them.
    """
    if not user or not user.is_authenticated or not user.has_perm("store.change_cuttingorder"):
        raise PermissionDenied("Not authorized to issue cutting orders.")

    order = CuttingOrder.objects.select_for_update().get(pk=cutting_order_id)
    roll = FabricRoll.objects.select_for_update().select_related("receipt").get(pk=order.roll_id)

    if order.status != CuttingOrder.Status.DRAFT:
        raise ValidationError("Only draft cutting orders can be issued.")
    if roll.receipt.status != "VERIFIED":
        raise ValidationError("Fabric receipt must be verified first.")
    if roll.location != FabricRoll.Location.RAW:
        raise ValidationError("This roll has already left raw material stock.")
    if roll.available_meters != roll.received_meters:
        raise ValidationError("Only a complete, unconsumed roll can be issued.")
    if not order.size_lines.exists():
        raise ValidationError("Enter the size-wise cutting plan before issuing.")

    roll.location = FabricRoll.Location.CUTTING
    roll.save(update_fields=["location"])
    order.status = CuttingOrder.Status.ISSUED
    order.save(update_fields=["status"])
    return order
