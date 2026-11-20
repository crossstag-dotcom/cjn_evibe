from django.db import models
from apps.store.models import Order


class DeadProductsReport(Order):
    """
    Proxy model for Dead Products Report
    No new database table created
    """

    class Meta:
        proxy = True
        verbose_name = "Dead Product"
        verbose_name_plural = "Dead Products Report"

    def __str__(self):
        return "Dead Products Report"