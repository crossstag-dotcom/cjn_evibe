"""Atomic size-wise dispatch of completed cut pieces to stitching."""
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Sum

from apps.store.models import CuttingCompletion, CuttingOrder, StitchingTransfer, StitchingTransferSize


@transaction.atomic
def issue_cut_pieces_to_stitching(*, completion_id, reference, recipient, sizes, user):
    if not user or not user.is_authenticated or not user.has_perm("store.add_stitchingtransfer"):
        raise PermissionDenied("Not authorized to issue stitching transfers.")
    reference = str(reference or "").strip()
    recipient = str(recipient or "").strip()
    if not reference or len(reference) > 80 or not recipient or len(recipient) > 160:
        raise ValidationError("Valid transfer reference and stitching recipient are required.")
    if not isinstance(sizes, dict) or not sizes:
        raise ValidationError("Enter at least one size quantity.")
    if any(not str(size).strip() or type(qty) is not int or qty <= 0 for size, qty in sizes.items()):
        raise ValidationError("Each issued size must have a positive whole-piece quantity.")

    # Lock the parent order to serialize all transfer requests for this cutting case.
    completion = CuttingCompletion.objects.select_related("order").get(pk=completion_id)
    order = CuttingOrder.objects.select_for_update().get(pk=completion.order_id)
    if order.status != CuttingOrder.Status.COMPLETED:
        raise ValidationError("Cutting must be completed before stitching issue.")
    if StitchingTransfer.objects.filter(reference=reference).exists():
        raise ValidationError("This stitching transfer reference already exists.")

    actual = dict(completion.size_lines.values_list("size", "actual_pieces"))
    if not set(sizes).issubset(actual):
        raise ValidationError("One or more sizes were not recorded in cutting completion.")
    already_issued = dict(
        StitchingTransferSize.objects.filter(
            transfer__cutting_completion=completion
        ).values("size").annotate(total=Sum("issued_pieces")).values_list("size", "total")
    )
    for size, qty in sizes.items():
        if qty + already_issued.get(size, 0) > actual[size]:
            raise ValidationError(f"Size {size}: issue exceeds remaining cut pieces.")

    transfer = StitchingTransfer.objects.create(
        cutting_completion=completion, reference=reference,
        recipient=recipient, issued_by=user,
    )
    StitchingTransferSize.objects.bulk_create([
        StitchingTransferSize(transfer=transfer, size=size, issued_pieces=qty)
        for size, qty in sizes.items()
    ])
    return transfer
