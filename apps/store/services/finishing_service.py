"""Finishing and rework services; never mutate saleable warehouse inventory."""
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from apps.store.models import (
    FinishingBatch, FinishingBatchSize, QualityInspection, ReworkTicket,
)


def _require(user, permission):
    if not user or not user.is_authenticated or not user.has_perm(permission):
        raise PermissionDenied("Not authorized for this finishing operation.")


@transaction.atomic
def open_finishing_batch(*, inspection_id, reference, user, notes=""):
    _require(user, "store.add_finishingbatch")
    reference = str(reference or "").strip()
    if not reference or len(reference) > 80 or not isinstance(notes, str):
        raise ValidationError("Valid finishing reference and notes are required.")
    inspection = QualityInspection.objects.select_for_update().get(pk=inspection_id)
    if inspection.status != QualityInspection.Status.POSTED:
        raise ValidationError("QC must be posted before finishing.")
    if FinishingBatch.objects.filter(inspection=inspection).exists():
        raise ValidationError("Finishing batch already exists for this QC inspection.")
    lines = list(inspection.size_lines.all())
    if not lines or not any(line.approved_pieces for line in lines):
        raise ValidationError("No QC-approved pieces are available for finishing.")
    batch = FinishingBatch.objects.create(
        inspection=inspection, reference=reference, notes=notes, created_by=user,
    )
    FinishingBatchSize.objects.bulk_create([
        FinishingBatchSize(batch=batch, size=line.size, approved_from_qc=line.approved_pieces)
        for line in lines if line.approved_pieces > 0
    ])
    return batch


@transaction.atomic
def complete_finishing_batch(*, batch_id, results, user):
    _require(user, "store.change_finishingbatch")
    batch = FinishingBatch.objects.select_for_update().get(pk=batch_id)
    if batch.status != FinishingBatch.Status.OPEN:
        raise ValidationError("Finishing has already been completed.")
    lines = list(FinishingBatchSize.objects.select_for_update().filter(batch=batch))
    if not isinstance(results, dict) or set(results) != {line.size for line in lines}:
        raise ValidationError("Provide finishing quantities for every approved size.")
    for line in lines:
        row = results[line.size]
        if not isinstance(row, dict) or set(row) != {"finished", "rework"}:
            raise ValidationError(f"Size {line.size}: finished and rework quantities are required.")
        finished, rework = row["finished"], row["rework"]
        if type(finished) is not int or type(rework) is not int or finished < 0 or rework < 0:
            raise ValidationError(f"Size {line.size}: quantities must be nonnegative integers.")
        if finished + rework > line.approved_from_qc:
            raise ValidationError(f"Size {line.size}: results exceed QC-approved pieces.")
        line.finished_pieces = finished
        line.finishing_rework_pieces = rework
    FinishingBatchSize.objects.bulk_update(lines, ["finished_pieces", "finishing_rework_pieces"])
    batch.status = FinishingBatch.Status.COMPLETED
    batch.completed_by = user
    batch.completed_at = timezone.now()
    batch.save(update_fields=["status", "completed_by", "completed_at"])
    return batch


@transaction.atomic
def open_qc_rework_ticket(*, inspection_id, reference, size, pieces, reason, user):
    _require(user, "store.add_reworkticket")
    reference, size, reason = (str(value or "").strip() for value in (reference, size, reason))
    if not reference or len(reference) > 80 or not size or len(size) > 12 or not reason or len(reason) > 240:
        raise ValidationError("Reference, size and repair reason are required.")
    if type(pieces) is not int or pieces <= 0:
        raise ValidationError("Rework pieces must be a positive integer.")
    inspection = QualityInspection.objects.select_for_update().get(pk=inspection_id)
    if inspection.status != QualityInspection.Status.POSTED:
        raise ValidationError("QC inspection must be posted.")
    qc_line = inspection.size_lines.filter(size=size).first()
    if qc_line is None:
        raise ValidationError("Size is not present in QC inspection.")
    allocated = ReworkTicket.objects.filter(inspection=inspection, size=size).aggregate(
        total=Sum("pieces")
    )["total"] or 0
    if allocated + pieces > qc_line.rework_pieces:
        raise ValidationError("Rework tickets exceed QC rework allocation.")
    return ReworkTicket.objects.create(
        inspection=inspection, reference=reference, size=size, pieces=pieces,
        reason=reason, created_by=user,
    )


@transaction.atomic
def mark_rework_repaired(*, ticket_id, user):
    _require(user, "store.change_reworkticket")
    ticket = ReworkTicket.objects.select_for_update().get(pk=ticket_id)
    if ticket.status != ReworkTicket.Status.OPEN:
        raise ValidationError("Rework ticket is already marked repaired.")
    ticket.status = ReworkTicket.Status.REPAIRED
    ticket.repaired_by = user
    ticket.repaired_at = timezone.now()
    ticket.save(update_fields=["status", "repaired_by", "repaired_at"])
    return ticket
