"""Permission-gated, atomic QC posting against received processing quantities."""
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.store.models import ProcessingBatch, QualityInspection, QualityInspectionSize


@transaction.atomic
def post_quality_inspection(*, processing_batch_id, reference, results, defect_notes="", user):
    if not user or not user.is_authenticated or not user.has_perm("store.add_qualityinspection"):
        raise PermissionDenied("Not authorized to post quality inspections.")

    reference = str(reference or "").strip()
    if not reference or len(reference) > 80:
        raise ValidationError("QC reference must contain 1 to 80 characters.")
    if not isinstance(defect_notes, str):
        raise ValidationError("Defect notes must be text.")
    if not isinstance(results, dict) or not results:
        raise ValidationError("Provide size-wise QC results.")

    batch = ProcessingBatch.objects.select_for_update().get(pk=processing_batch_id)
    if batch.status != ProcessingBatch.Status.RECEIVED:
        raise ValidationError("Processing receipt must be confirmed before QC.")
    if QualityInspection.objects.filter(processing_batch=batch).exists():
        raise ValidationError("This processing batch already has a QC inspection.")
    if QualityInspection.objects.filter(reference=reference).exists():
        raise ValidationError("QC reference already exists.")

    received = {line.size: line.received_pieces for line in batch.size_lines.all()}
    if not received or any(value is None for value in received.values()) or set(results) != set(received):
        raise ValidationError("Provide QC results for every received processing size.")

    normalized = []
    for size, row in results.items():
        if not isinstance(row, dict) or set(row) != {"inspected", "approved", "rework", "rejected"}:
            raise ValidationError(f"Size {size}: expected inspected, approved, rework, rejected.")
        if any(type(value) is not int or value < 0 for value in row.values()):
            raise ValidationError(f"Size {size}: quantities must be nonnegative integers.")
        if row["inspected"] > received[size]:
            raise ValidationError(f"Size {size}: inspected exceeds processing receipt.")
        if row["inspected"] != row["approved"] + row["rework"] + row["rejected"]:
            raise ValidationError(f"Size {size}: QC outcomes must equal inspected pieces.")
        normalized.append((size, row))

    if not any(row["inspected"] for _, row in normalized):
        raise ValidationError("Cannot post an empty QC inspection.")

    inspection = QualityInspection.objects.create(
        processing_batch=batch, reference=reference, defect_notes=defect_notes,
        status=QualityInspection.Status.POSTED, created_by=user,
        posted_by=user, posted_at=timezone.now(),
    )
    QualityInspectionSize.objects.bulk_create([
        QualityInspectionSize(
            inspection=inspection, size=size,
            inspected_pieces=row["inspected"], approved_pieces=row["approved"],
            rework_pieces=row["rework"], rejected_pieces=row["rejected"],
        )
        for size, row in normalized
    ])
    return inspection
