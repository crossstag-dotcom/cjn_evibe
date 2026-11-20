"""Finishing receipts from QC-approved pieces; no warehouse posting."""
from django.conf import settings
from django.db import models
from django.db.models import Q


class FinishingBatch(models.Model):
    class Status(models.TextChoices):
        OPEN = "OPEN", "In finishing"
        COMPLETED = "COMPLETED", "Finishing completed"

    inspection = models.OneToOneField(
        "store.QualityInspection", on_delete=models.PROTECT, related_name="finishing_batch"
    )
    reference = models.CharField(max_length=80, unique=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.OPEN)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="finishing_batches_created"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT,
        related_name="finishing_batches_completed"
    )
    completed_at = models.DateTimeField(null=True, blank=True)


class FinishingBatchSize(models.Model):
    batch = models.ForeignKey(FinishingBatch, on_delete=models.PROTECT, related_name="size_lines")
    size = models.CharField(max_length=12)
    approved_from_qc = models.PositiveIntegerField()
    finished_pieces = models.PositiveIntegerField(null=True, blank=True)
    finishing_rework_pieces = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["batch", "size"], name="unique_finishing_batch_size"),
            models.CheckConstraint(
                condition=Q(finished_pieces__isnull=True) | Q(finished_pieces__lte=models.F("approved_from_qc")),
                name="finishing_not_above_qc_approved",
            ),
        ]


class ReworkTicket(models.Model):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Awaiting repair"
        REPAIRED = "REPAIRED", "Repaired; awaiting QC"

    inspection = models.ForeignKey(
        "store.QualityInspection", on_delete=models.PROTECT, related_name="rework_tickets"
    )
    reference = models.CharField(max_length=80, unique=True)
    size = models.CharField(max_length=12)
    pieces = models.PositiveIntegerField()
    reason = models.CharField(max_length=240)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.OPEN)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="rework_tickets_created"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    repaired_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT,
        related_name="rework_tickets_repaired"
    )
    repaired_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(pieces__gt=0), name="rework_ticket_pieces_positive"),
        ]
