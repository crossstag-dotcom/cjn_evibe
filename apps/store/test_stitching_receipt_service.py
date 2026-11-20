from decimal import Decimal
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.store.models import (
    FabricReceipt, FabricRoll, CuttingOrder, CuttingCompletion,
    StitchingTransfer, StitchingTransferSize,
)
from apps.store.services.stitching_receipt_service import confirm_stitching_receipt


class StitchingReceiptTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="stitching_receipt_tester", password="test-password"
        )
        self.user.user_permissions.add(Permission.objects.get(codename="change_stitchingtransfer"))
        receipt = FabricReceipt.objects.create(
            supplier_name="Test Supplier", dc_number="ST-RECEIPT",
            status=FabricReceipt.Status.VERIFIED, created_by=self.user,
        )
        roll = FabricRoll.objects.create(
            receipt=receipt, supplier_roll_number="438939", fabric_description="Denim",
            received_meters=Decimal("122"), available_meters=Decimal("2"),
            location=FabricRoll.Location.CUTTING,
        )
        order = CuttingOrder.objects.create(
            case_number="635", cutting_master="Master", roll=roll,
            status=CuttingOrder.Status.COMPLETED, created_by=self.user,
        )
        completion = CuttingCompletion.objects.create(
            order=order, consumed_meters=Decimal("119"),
            waste_meters=Decimal("1"), leftover_meters=Decimal("2"),
            completed_by=self.user,
        )
        self.transfer = StitchingTransfer.objects.create(
            cutting_completion=completion, reference="ST-R-1",
            recipient="Stitching Unit A", issued_by=self.user,
        )
        for size in ("28", "30"):
            StitchingTransferSize.objects.create(
                transfer=self.transfer, size=size, issued_pieces=21,
            )

    def test_full_receipt(self):
        confirm_stitching_receipt(
            transfer_id=self.transfer.pk, received_sizes={"28": 21, "30": 21}, user=self.user
        )
        self.transfer.refresh_from_db()
        self.assertEqual(self.transfer.status, StitchingTransfer.Status.RECEIVED)
        self.assertIsNotNone(self.transfer.received_at)

    def test_shortage_is_preserved(self):
        confirm_stitching_receipt(
            transfer_id=self.transfer.pk, received_sizes={"28": 20, "30": 21}, user=self.user
        )
        lines = dict(self.transfer.size_lines.values_list("size", "received_pieces"))
        self.assertEqual(lines, {"28": 20, "30": 21})

    def test_duplicate_confirmation_rejected(self):
        kwargs = dict(transfer_id=self.transfer.pk, received_sizes={"28": 21, "30": 21}, user=self.user)
        confirm_stitching_receipt(**kwargs)
        with self.assertRaises(ValidationError):
            confirm_stitching_receipt(**kwargs)

    def test_overreceipt_rejected(self):
        with self.assertRaises(ValidationError):
            confirm_stitching_receipt(
                transfer_id=self.transfer.pk, received_sizes={"28": 22, "30": 21}, user=self.user
            )
        self.transfer.refresh_from_db()
        self.assertEqual(self.transfer.status, StitchingTransfer.Status.ISSUED)
