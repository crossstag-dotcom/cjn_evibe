from django.db import models
from .order import Order

class AnalyticsDashboard(Order):
    """
    Proxy model used only for displaying
    the analytics dashboard inside Django admin.
    No database table will be created.
    """

    class Meta:
        proxy = True
        verbose_name = "Dashboard"
        verbose_name_plural = "Analytics"