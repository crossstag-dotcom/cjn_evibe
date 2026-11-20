"""Read-only, size-wise reconciliation of cutting and stitching custody.

This service reports discrepancies without creating inventory adjustments.
"""
from django.core.exceptions import ValidationError
from django.db.models import Sum

from apps.store.models import CuttingCompletion, StitchingTransferSize


def cutting_to_stitching_reconciliation(*, completion_id):
    completion = CuttingCompletion.objects.select_related("order").get(pk=completion_id)
    actual = dict(completion.size_lines.values_list("size", "actual_pieces"))
    if not actual:
        raise ValidationError("Cutting completion has no recorded size quantities.")

    lines = (
        StitchingTransferSize.objects.filter(transfer__cutting_completion_id=completion_id)
        .values("size", "transfer__status")
        .annotate(issued=Sum("issued_pieces"), received=Sum("received_pieces"))
    )
    issued = {size: 0 for size in actual}
    received = {size: 0 for size in actual}
    pending = {size: 0 for size in actual}
    shortage = {size: 0 for size in actual}

    for line in lines:
        size = line["size"]
        if size not in actual:
            raise ValidationError(f"Unexpected transfer size {size}.")
        qty = line["issued"]
        issued[size] += qty
        if line["transfer__status"] == "RECEIVED":
            if line["received"] is None:
                raise ValidationError(f"Received transfer missing receipt count for size {size}.")
            received[size] += line["received"]
            shortage[size] += qty - line["received"]
        elif line["transfer__status"] == "ISSUED":
            pending[size] += qty
        else:
            raise ValidationError("Unrecognized stitching transfer status.")

    sizes = {}
    for size, cut in actual.items():
        if issued[size] > cut:
            raise ValidationError(f"Size {size}: issued pieces exceed cut output.")
        if shortage[size] < 0:
            raise ValidationError(f"Size {size}: receipt exceeds issued pieces.")
        sizes[size] = {
            "cut": cut,
            "issued": issued[size],
            "remaining_in_cutting": cut - issued[size],
            "received": received[size],
            "in_transit": pending[size],
            "receipt_shortage": shortage[size],
        }

    totals = {key: sum(row[key] for row in sizes.values()) for key in next(iter(sizes.values()))}
    return {
        "cutting_case": completion.order.case_number,
        "sizes": sizes,
        "totals": totals,
        "balanced": (
            totals["cut"] == totals["remaining_in_cutting"] + totals["issued"]
            and totals["issued"] == totals["received"] + totals["in_transit"] + totals["receipt_shortage"]
        ),
    }
