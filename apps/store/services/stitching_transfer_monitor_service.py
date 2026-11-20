"""Read-only monitoring of stitching dispatches awaiting receipt.

Issued cut pieces remain work-in-progress and must never be counted as saleable stock.
"""
from django.core.exceptions import ValidationError

from apps.store.models import StitchingTransfer


def get_pending_stitching_transfers(*, limit=100):
    if type(limit) is not int or not 1 <= limit <= 200:
        raise ValidationError("Limit must be an integer between 1 and 200.")

    transfers = (
        StitchingTransfer.objects.filter(status=StitchingTransfer.Status.ISSUED)
        .select_related("cutting_completion__order")
        .prefetch_related("size_lines")
        .order_by("issued_at", "pk")[:limit]
    )
    results = []
    for transfer in transfers:
        sizes = {
            line.size: line.issued_pieces
            for line in sorted(transfer.size_lines.all(), key=lambda item: item.size)
        }
        results.append({
            "transfer_id": transfer.pk,
            "reference": transfer.reference,
            "cutting_completion_id": transfer.cutting_completion_id,
            "cutting_case": transfer.cutting_completion.order.case_number,
            "recipient": transfer.recipient,
            "issued_at": transfer.issued_at.isoformat(),
            "sizes": sizes,
            "total_issued_pieces": sum(sizes.values()),
            "status": transfer.status,
        })
    return results
