"""Washing/processing custody of stitched pieces, separate from saleable stock."""
from django.conf import settings
from django.db import models
from django.db.models import Q


class ProcessingBatch(models.Model):
    class Status(models.TextChoices):
        ISSUED = "ISSUED", "Sent for washing/processing"
        RECEIVED = "RECEIVED", "Received from processing"

    reference = models.CharField(max_length=80, unique=True)
    stitching_transfer = models.OneToOneField(
        "store.StitchingTransfer", on_delete=models.PROTECT, related_name="processing_batch"
    )
    processor = models.CharField(max_length=160)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.ISSUED)
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="processing_issues"
    )
    issued_at = models.DateTimeField(auto_now_add=True)
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT,
        related_name="processing_receipts"
    )
    received_at = models.DateTimeField(null=True, blank=True)


class ProcessingBatchSize(models.Model):
    batch = models.ForeignKey(ProcessingBatch, on_delete=models.PROTECT, related_name="size_lines")
    size = models.CharField(max_length=12)
    issued_pieces = models.PositiveIntegerField()
    received_pieces = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["batch", "size"], name="unique_processing_batch_size"),
            models.CheckConstraint(condition=Q(issued_pieces__gt=0), name="processing_issued_positive"),
            models.CheckConstraint(
                condition=Q(received_pieces__isnull=True) | Q(received_pieces__gte=0),
                name="processing_received_nonnegative",
            ),
        ]
