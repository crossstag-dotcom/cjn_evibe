from django.db import models
from apps.store.models import Order


class CityRevenueIntelligence(Order):
    """
    Proxy model for
    City Wise Revenue Intelligence

    No database table created
    """

    class Meta:
        proxy = True
        verbose_name = "City Revenue Intelligence"
        verbose_name_plural = "City Wise Revenue Intelligence"

    def __str__(self):
        return "City Wise Revenue Intelligence"