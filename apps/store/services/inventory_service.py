from django.db import transaction
from ..models import ProductVariant

# -----------------------
# FULL STOCK RESTORE (CANCELLED)
# -----------------------
def restore_full_stock(order):

        for item in order.items.select_related('variant'):

            variant = ProductVariant.objects.select_for_update().get(
                id=item.variant.id
            )

            variant.stock += item.quantity
            variant.save()


# -----------------------
# PARTIAL STOCK RESTORE (RETURN)
# -----------------------
def restore_partial_stock(order):

        for item in order.items.select_related('variant'):

            qty = item.returned_quantity

            if qty > 0:

                variant = ProductVariant.objects.select_for_update().get(
                    id=item.variant.id
                )

                variant.stock += qty
                variant.save()