from django.db import models
from django.utils import timezone


class ProductView(models.Model):

    product = models.ForeignKey(
        "store.Product",
        on_delete=models.CASCADE,
        related_name="product_views"
    )

    session_id = models.CharField(max_length=255, db_index=True)

    city = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=["product", "session_id"]),
        ]

    def __str__(self):
        return f"{self.product.name} - {self.session_id}"