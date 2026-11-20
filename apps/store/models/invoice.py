from django.db import models

from .order import Order


class Invoice(models.Model):

    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name="invoice"
    )

    invoice_number = models.CharField(
        max_length=50,
        unique=True
    )

    invoice_pdf = models.FileField(
        upload_to="invoices/",
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return self.invoice_number