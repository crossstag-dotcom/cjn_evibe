"""Confirm stitching receipt, preserving size-wise discrepancies."""
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.store.models import StitchingTransfer, StitchingTransferSize


@transaction.atomic
def confirm_stitching_receipt(*, transfer_id, received_sizes, user):
    """Receive a dispatched batch once; discrepancies remain visible."""
    if not user or not user.is_authenticated or not user.has_perm("store.change_stitchingtransfer"):
        raise PermissionDenied("Not authorized to confirm stitching receipt.")

    transfer = StitchingTransfer.objects.select_for_update().get(pk=transfer_id)
    if transfer.status != StitchingTransfer.Status.ISSUED:
        raise ValidationError("Only issued transfers can be received.")
    lines = list(StitchingTransferSize.objects.select_for_update().filter(transfer=transfer))
    expected = {line.size for line in lines}
    if not isinstance(received_sizes, dict) or set(received_sizes) != expected:
        raise ValidationError("Enter received quantities for every dispatched size.")
    for line in lines:
        count = received_sizes[line.size]
        if type(count) is not int or count < 0:
            raise ValidationError("Received pieces must be nonnegative whole numbers.")
        if count > line.issued_pieces:
            raise ValidationError(
                f"Size {line.size}: received pieces exceed issued quantity; investigate discrepancy."
            )

    for line in lines:
        line.received_pieces = received_sizes[line.size]
    StitchingTransferSize.objects.bulk_update(lines, ["received_pieces"])
    transfer.status = StitchingTransfer.Status.RECEIVED
    transfer.received_by = user
    transfer.received_at = timezone.now()
    transfer.save(update_fields=["status", "received_by", "received_at"])
    return transfer
