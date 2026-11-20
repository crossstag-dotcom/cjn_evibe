"""Guardrail tests for finished-goods receipt posting."""
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import SimpleTestCase

from apps.store.services.finished_goods_receipt_service import post_finished_goods_receipt


class AllowedUser:
    is_authenticated = True

    def has_perm(self, permission):
        return True


class FinishedGoodsReceiptGuardrailTests(SimpleTestCase):
    def test_anonymous_cannot_post(self):
        with self.assertRaises(PermissionDenied):
            post_finished_goods_receipt(
                finishing_size_id=1, variant_id=1, quantity=10,
                reference="FG-001", user=None,
            )

    def test_invalid_reference_rejected_before_database_access(self):
        with self.assertRaises(ValidationError):
            post_finished_goods_receipt(
                finishing_size_id=1, variant_id=1, quantity=10,
                reference="", user=AllowedUser(),
            )

    def test_zero_quantity_rejected_before_database_access(self):
        with self.assertRaises(ValidationError):
            post_finished_goods_receipt(
                finishing_size_id=1, variant_id=1, quantity=0,
                reference="FG-001", user=AllowedUser(),
            )

    def test_boolean_quantity_rejected_before_database_access(self):
        with self.assertRaises(ValidationError):
            post_finished_goods_receipt(
                finishing_size_id=1, variant_id=1, quantity=True,
                reference="FG-001", user=AllowedUser(),
            )
