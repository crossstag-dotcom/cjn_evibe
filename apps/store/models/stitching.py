"""Size-wise cut-piece dispatches to stitching (not finished-goods stock)."""
from django.conf import settings
from django.db import models
from django.db.models import Q


class StitchingTransfer(models.Model):
    class Status(models.TextChoices):
        ISSUED = "ISSUED", "Issued"
        RECEIVED = "RECEIVED", "Received"

    cutting_completion = models.ForeignKey(
        "store.CuttingCompletion", on_delete=models.PROTECT, related_name="stitching_transfers"
    )
    reference = models.CharField(max_length=80, unique=True)
    recipient = models.CharField(max_length=160)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.ISSUED)
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="stitching_issues"
    )
    issued_at = models.DateTimeField(auto_now_add=True)
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT,
        related_name="stitching_receipts"
    )
    received_at = models.DateTimeField(null=True, blank=True)


class StitchingTransferSize(models.Model):
    transfer = models.ForeignKey(StitchingTransfer, on_delete=models.PROTECT, related_name="size_lines")
    size = models.CharField(max_length=12)
    issued_pieces = models.PositiveIntegerField()
    received_pieces = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["transfer", "size"], name="unique_stitching_transfer_size"),
            models.CheckConstraint(condition=Q(issued_pieces__gt=0), name="stitching_issued_positive"),
            models.CheckConstraint(
                condition=Q(received_pieces__isnull=True) | Q(received_pieces__gte=0),
                name="stitching_received_nonnegative"
            ),
        ]
