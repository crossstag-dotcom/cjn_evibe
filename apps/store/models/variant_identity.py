"""Optional SKU/colour identity for existing ProductVariant records.

One-to-one mapping preserves existing catalog and order foreign keys.
"""
from django.db import models


class VariantIdentity(models.Model):
    variant = models.OneToOneField(
        "store.ProductVariant", on_delete=models.PROTECT, related_name="identity"
    )
    sku = models.CharField(max_length=100, unique=True)
    colour = models.CharField(max_length=100)
    article_code = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.sku
