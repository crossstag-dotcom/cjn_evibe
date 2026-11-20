"""Read-only production counts for the existing Django admin dashboard.

Cutting pieces and stitching receipts are work-in-progress, not saleable stock.
"""
from django.db.models import Sum
from apps.store.models import CuttingCompletionSize, StitchingTransferSize, StitchingTransfer


def get_manufacturing_summary():
    cut = CuttingCompletionSize.objects.aggregate(total=Sum("actual_pieces"))["total"] or 0
    issued = StitchingTransferSize.objects.aggregate(total=Sum("issued_pieces"))["total"] or 0
    received = (
        StitchingTransferSize.objects.filter(transfer__status=StitchingTransfer.Status.RECEIVED)
        .aggregate(total=Sum("received_pieces"))["total"] or 0
    )
    in_transit = (
        StitchingTransferSize.objects.filter(transfer__status=StitchingTransfer.Status.ISSUED)
        .aggregate(total=Sum("issued_pieces"))["total"] or 0
    )
    shortage = issued - received - in_transit
    remaining = cut - issued
    return {
        "cut_pieces": cut,
        "issued_to_stitching": issued,
        "received_at_stitching": received,
        "in_transit": in_transit,
        "receipt_shortage": shortage,
        "remaining_in_cutting": remaining,
        "reconciliation_ok": remaining >= 0 and shortage >= 0,
    }
