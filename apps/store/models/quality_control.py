"""QC of received processing batches. No finished-goods inventory posting."""
from django.conf import settings
from django.db import models
from django.db.models import Q


class QualityInspection(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        POSTED = "POSTED", "Posted"

    processing_batch = models.OneToOneField(
        "store.ProcessingBatch", on_delete=models.PROTECT, related_name="quality_inspection"
    )
    reference = models.CharField(max_length=80, unique=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT)
    defect_notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="quality_inspections_created"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    posted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT,
        related_name="quality_inspections_posted"
    )
    posted_at = models.DateTimeField(null=True, blank=True)


class QualityInspectionSize(models.Model):
    inspection = models.ForeignKey(QualityInspection, on_delete=models.PROTECT, related_name="size_lines")
    size = models.CharField(max_length=12)
    inspected_pieces = models.PositiveIntegerField()
    approved_pieces = models.PositiveIntegerField()
    rework_pieces = models.PositiveIntegerField()
    rejected_pieces = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["inspection", "size"], name="unique_quality_inspection_size"),
            models.CheckConstraint(
                condition=Q(inspected_pieces=models.F("approved_pieces") + models.F("rework_pieces") + models.F("rejected_pieces")),
                name="qc_outcomes_equal_inspected",
            ),
        ]
