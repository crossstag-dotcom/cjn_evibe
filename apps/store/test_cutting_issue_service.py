from decimal import Decimal
from unittest.mock import Mock
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.store.models import FabricReceipt, FabricRoll, CuttingOrder, CuttingOrderSize
from apps.store.services.cutting_issue_service import issue_complete_roll_to_cutting


class CuttingIssueTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="cutting_tester", password="test-password")
        self.receipt = FabricReceipt.objects.create(
            supplier_name="Test Supplier", dc_number="DC-1", status=FabricReceipt.Status.VERIFIED,
            created_by=self.user,
        )
        self.roll = FabricRoll.objects.create(
            receipt=self.receipt, supplier_roll_number="438939",
            fabric_description="Test denim", received_meters=Decimal("122"),
            available_meters=Decimal("122"),
        )
        self.order = CuttingOrder.objects.create(
            case_number="635", cutting_master="Test Master", roll=self.roll,
            planned_average_meters=Decimal("1.16"), created_by=self.user,
        )
        for size in ("28", "30", "32", "34", "36"):
            CuttingOrderSize.objects.create(order=self.order, size=size, planned_pieces=21)
        self.authorized = Mock(is_authenticated=True)
        self.authorized.has_perm.return_value = True

    def test_issues_full_roll_without_consuming_meters(self):
        issue_complete_roll_to_cutting(cutting_order_id=self.order.pk, user=self.authorized)
        self.roll.refresh_from_db()
        self.order.refresh_from_db()
        self.assertEqual(self.roll.location, FabricRoll.Location.CUTTING)
        self.assertEqual(self.roll.available_meters, Decimal("122"))
        self.assertEqual(self.order.status, CuttingOrder.Status.ISSUED)

    def test_double_issue_rejected(self):
        issue_complete_roll_to_cutting(cutting_order_id=self.order.pk, user=self.authorized)
        with self.assertRaises(ValidationError):
            issue_complete_roll_to_cutting(cutting_order_id=self.order.pk, user=self.authorized)

    def test_unverified_receipt_rejected(self):
        self.receipt.status = FabricReceipt.Status.DRAFT
        self.receipt.save(update_fields=["status"])
        with self.assertRaises(ValidationError):
            issue_complete_roll_to_cutting(cutting_order_id=self.order.pk, user=self.authorized)

    def test_unauthorized_issue_rejected(self):
        with self.assertRaises(PermissionDenied):
            issue_complete_roll_to_cutting(cutting_order_id=self.order.pk, user=self.user)
