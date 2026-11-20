"""Fabric receipt and cutting-order records.

Draft records do not change inventory. Posting/issuing requires separate
transactional services, permissions, and verified physical quantities.
"""
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q


class FabricReceipt(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        VERIFIED = "VERIFIED", "Verified"
        CANCELLED = "CANCELLED", "Cancelled"

    supplier_name = models.CharField(max_length=160)
    dc_number = models.CharField(max_length=80)
    dc_date = models.DateField(null=True, blank=True)
    dc_image = models.ImageField(upload_to="fabric/dc/", blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["supplier_name", "dc_number"], name="unique_supplier_fabric_dc"),
        ]

    def __str__(self):
        return f"{self.supplier_name} / {self.dc_number}"


class FabricRoll(models.Model):
    class Location(models.TextChoices):
        RAW = "RAW", "Raw material stock"
        CUTTING = "CUTTING", "Cutting department"

    receipt = models.ForeignKey(FabricReceipt, on_delete=models.PROTECT, related_name="rolls")
    supplier_roll_number = models.CharField(max_length=100)
    fabric_description = models.CharField(max_length=160)
    received_meters = models.DecimalField(max_digits=11, decimal_places=3, validators=[MinValueValidator(0.001)])
    available_meters = models.DecimalField(max_digits=11, decimal_places=3, validators=[MinValueValidator(0)])
    location = models.CharField(max_length=12, choices=Location.choices, default=Location.RAW)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["receipt", "supplier_roll_number"], name="unique_roll_per_fabric_dc"),
            models.CheckConstraint(condition=Q(received_meters__gt=0), name="fabric_roll_received_positive"),
            models.CheckConstraint(condition=Q(available_meters__gte=0), name="fabric_roll_available_nonnegative"),
            models.CheckConstraint(condition=Q(available_meters__lte=models.F("received_meters")), name="fabric_roll_available_not_above_received"),
        ]

    def __str__(self):
        return self.supplier_roll_number


class CuttingOrder(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        ISSUED = "ISSUED", "Issued to cutting"
        COMPLETED = "COMPLETED", "Cutting completed"
        CANCELLED = "CANCELLED", "Cancelled"

    case_number = models.CharField(max_length=80)
    cutting_master = models.CharField(max_length=160)
    roll = models.ForeignKey(FabricRoll, on_delete=models.PROTECT, related_name="cutting_orders")
    planned_average_meters = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cutting case {self.case_number}"


class CuttingOrderSize(models.Model):
    order = models.ForeignKey(CuttingOrder, on_delete=models.CASCADE, related_name="size_lines")
    size = models.CharField(max_length=12)
    planned_pieces = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["order", "size"], name="unique_cutting_order_size"),
            models.CheckConstraint(condition=Q(planned_pieces__gt=0), name="cutting_size_pieces_positive"),
        ]


class CuttingCompletion(models.Model):
    """Posted actuals; one final completion per cutting order."""
    order = models.OneToOneField(CuttingOrder, on_delete=models.PROTECT, related_name="completion")
    consumed_meters = models.DecimalField(max_digits=11, decimal_places=3)
    waste_meters = models.DecimalField(max_digits=11, decimal_places=3)
    leftover_meters = models.DecimalField(max_digits=11, decimal_places=3)
    completed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(consumed_meters__gte=0), name="cutting_consumed_nonnegative"),
            models.CheckConstraint(condition=Q(waste_meters__gte=0), name="cutting_waste_nonnegative"),
            models.CheckConstraint(condition=Q(leftover_meters__gte=0), name="cutting_leftover_nonnegative"),
        ]


class CuttingCompletionSize(models.Model):
    completion = models.ForeignKey(CuttingCompletion, on_delete=models.PROTECT, related_name="size_lines")
    size = models.CharField(max_length=12)
    actual_pieces = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["completion", "size"], name="unique_cutting_completion_size"),
        ]
