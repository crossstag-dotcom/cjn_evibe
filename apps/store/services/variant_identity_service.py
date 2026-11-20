"""Explicit, permission-controlled identity assignment; no generated SKU guesses."""
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from apps.store.models import ProductVariant, VariantIdentity


@transaction.atomic
def assign_variant_identity(*, variant_id, sku, colour, article_code, user):
    if not user or not user.is_authenticated or not user.has_perm("store.add_variantidentity"):
        raise PermissionDenied("Not authorized to assign SKU identities.")
    sku, colour, article_code = (
        str(value or "").strip() for value in (sku, colour, article_code)
    )
    if not sku or len(sku) > 100 or not colour or len(colour) > 100 or not article_code or len(article_code) > 100:
        raise ValidationError("Valid SKU, colour and article code are required.")

    variant = ProductVariant.objects.select_for_update().select_related("product").get(pk=variant_id)
    if variant.product.product_code != article_code:
        raise ValidationError("Article code must match the linked product's existing product code.")
    if VariantIdentity.objects.filter(variant=variant).exists():
        raise ValidationError("This variant already has an identity; changes require a separate reviewed workflow.")
    if VariantIdentity.objects.filter(sku__iexact=sku).exists():
        raise ValidationError("SKU already assigned to another variant.")
    return VariantIdentity.objects.create(
        variant=variant, sku=sku, colour=colour, article_code=article_code,
    )
