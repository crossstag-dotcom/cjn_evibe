from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.store.models import (
    FabricReceipt, FabricRoll, CuttingOrder, CuttingOrderSize, CuttingCompletion,
)
from apps.store.services.cutting_completion_service import complete_cutting


class CuttingCompletionTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="completion_tester", password="test-password"
        )
        self.user.user_permissions.add(Permission.objects.get(codename="change_cuttingorder"))
        receipt = FabricReceipt.objects.create(
            supplier_name="Test Supplier", dc_number="DC-COMPLETE",
            status=FabricReceipt.Status.VERIFIED, created_by=self.user,
        )
        self.roll = FabricRoll.objects.create(
            receipt=receipt, supplier_roll_number="438939",
            fabric_description="Test fabric", received_meters=Decimal("122"),
            available_meters=Decimal("122"), location=FabricRoll.Location.CUTTING,
        )
        self.order = CuttingOrder.objects.create(
            case_number="635", cutting_master="Cutting Master",
            roll=self.roll, status=CuttingOrder.Status.ISSUED, created_by=self.user,
        )
        for size in ("28", "30", "32", "34", "36"):
            CuttingOrderSize.objects.create(order=self.order, size=size, planned_pieces=21)
        self.sizes = {size: 21 for size in ("28", "30", "32", "34", "36")}

    def test_completion_preserves_leftover_in_cutting(self):
        completion = complete_cutting(
            cutting_order_id=self.order.pk, actual_sizes=self.sizes,
            consumed_meters="119", waste_meters="1", user=self.user,
        )
        self.roll.refresh_from_db()
        self.order.refresh_from_db()
        self.assertEqual(completion.leftover_meters, Decimal("2"))
        self.assertEqual(self.roll.available_meters, Decimal("2"))
        self.assertEqual(self.roll.location, FabricRoll.Location.CUTTING)
        self.assertEqual(self.order.status, CuttingOrder.Status.COMPLETED)
        self.assertEqual(sum(completion.size_lines.values_list("actual_pieces", flat=True)), 105)

    def test_cannot_complete_twice(self):
        kwargs = dict(cutting_order_id=self.order.pk, actual_sizes=self.sizes,
                      consumed_meters="119", waste_meters="1", user=self.user)
        complete_cutting(**kwargs)
        with self.assertRaises(ValidationError):
            complete_cutting(**kwargs)
        self.assertEqual(CuttingCompletion.objects.filter(order=self.order).count(), 1)

    def test_overconsumption_does_not_change_stock(self):
        with self.assertRaises(ValidationError):
            complete_cutting(
                cutting_order_id=self.order.pk, actual_sizes=self.sizes,
                consumed_meters="122", waste_meters="1", user=self.user,
            )
        self.roll.refresh_from_db()
        self.assertEqual(self.roll.available_meters, Decimal("122"))
        self.assertFalse(CuttingCompletion.objects.filter(order=self.order).exists())

    def test_missing_size_rejected(self):
        with self.assertRaises(ValidationError):
            complete_cutting(
                cutting_order_id=self.order.pk, actual_sizes={"32": 21},
                consumed_meters="119", waste_meters="1", user=self.user,
            )
