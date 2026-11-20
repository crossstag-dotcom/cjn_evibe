"""Atomic issue and receipt for washing/processing, with size-wise custody."""
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.store.models import ProcessingBatch, ProcessingBatchSize, StitchingTransfer


def _require(user, permission):
    if not user or not user.is_authenticated or not user.has_perm(permission):
        raise PermissionDenied("Not authorized for this processing operation.")


@transaction.atomic
def issue_processing_batch(*, stitching_transfer_id, reference, processor, user):
    _require(user, "store.add_processingbatch")
    reference = str(reference or "").strip()
    processor = str(processor or "").strip()
    if not reference or len(reference) > 80 or not processor or len(processor) > 160:
        raise ValidationError("Valid batch reference and processor are required.")

    transfer = StitchingTransfer.objects.select_for_update().get(pk=stitching_transfer_id)
    if transfer.status != StitchingTransfer.Status.RECEIVED:
        raise ValidationError("Stitching transfer must be received before processing issue.")
    if ProcessingBatch.objects.filter(stitching_transfer=transfer).exists():
        raise ValidationError("This stitching transfer already has a processing batch.")
    if ProcessingBatch.objects.filter(reference=reference).exists():
        raise ValidationError("Processing batch reference already exists.")

    lines = list(transfer.size_lines.order_by("size"))
    if not lines or any(line.received_pieces is None for line in lines):
        raise ValidationError("Stitching receipt quantities must be recorded for every size.")
    issued = [line for line in lines if line.received_pieces > 0]
    if not issued:
        raise ValidationError("No received stitched pieces available for processing.")

    batch = ProcessingBatch.objects.create(
        reference=reference, stitching_transfer=transfer, processor=processor, issued_by=user
    )
    ProcessingBatchSize.objects.bulk_create([
        ProcessingBatchSize(batch=batch, size=line.size, issued_pieces=line.received_pieces)
        for line in issued
    ])
    return batch


@transaction.atomic
def confirm_processing_receipt(*, batch_id, received_sizes, user):
    _require(user, "store.change_processingbatch")
    batch = ProcessingBatch.objects.select_for_update().get(pk=batch_id)
    if batch.status != ProcessingBatch.Status.ISSUED:
        raise ValidationError("Processing batch was already received.")
    lines = list(ProcessingBatchSize.objects.select_for_update().filter(batch=batch))
    if not isinstance(received_sizes, dict) or set(received_sizes) != {line.size for line in lines}:
        raise ValidationError("Provide received quantities for every issued size.")
    for line in lines:
        qty = received_sizes[line.size]
        if type(qty) is not int or qty < 0 or qty > line.issued_pieces:
            raise ValidationError(f"Invalid received quantity for size {line.size}.")
        line.received_pieces = qty
    ProcessingBatchSize.objects.bulk_update(lines, ["received_pieces"])
    batch.status = ProcessingBatch.Status.RECEIVED
    batch.received_by = user
    batch.received_at = timezone.now()
    batch.save(update_fields=["status", "received_by", "received_at"])
    return batch
