"""Validation checks for assigning identity without changing existing products."""
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import SimpleTestCase

from apps.store.services.variant_identity_service import assign_variant_identity


class AuthorizedIdentityUser:
    is_authenticated = True

    def has_perm(self, permission):
        return permission == "store.add_variantidentity"


class VariantIdentityGuardrailTests(SimpleTestCase):
    def test_permission_required(self):
        with self.assertRaises(PermissionDenied):
            assign_variant_identity(
                variant_id=1, sku="EV-BLK-32", colour="Black",
                article_code="EV-STR", user=None,
            )

    def test_missing_sku_is_rejected(self):
        with self.assertRaises(ValidationError):
            assign_variant_identity(
                variant_id=1, sku="", colour="Black",
                article_code="EV-STR", user=AuthorizedIdentityUser(),
            )

    def test_missing_colour_is_rejected(self):
        with self.assertRaises(ValidationError):
            assign_variant_identity(
                variant_id=1, sku="EV-BLK-32", colour="",
                article_code="EV-STR", user=AuthorizedIdentityUser(),
            )
