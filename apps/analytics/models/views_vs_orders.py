from django.db import models
from apps.store.models import Order


class ViewsVsOrders(Order):
    """
    Proxy model for Views vs Orders admin page
    No database table will be created
    """

    class Meta:
        proxy = True
        verbose_name = "Views vs Orders"
        verbose_name_plural = "Views vs Orders"

    def __str__(self):
        return "Views vs Orders"