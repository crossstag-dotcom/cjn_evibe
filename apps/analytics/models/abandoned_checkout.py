from django.db import models
from apps.store.models import Order


class AbandonedCheckout(Order):
    """
    Proxy model for payment Drop-off admin page
    No new database table will be created
    """

    class Meta:
        proxy = True
        verbose_name = "payment Drop-off"
        verbose_name_plural = "payment Drop-off"

    def __str__(self):
        return "payment Drop-off"