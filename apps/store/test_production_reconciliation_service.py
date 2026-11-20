from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.core.exceptions import ValidationError

from apps.store.models import (
    FabricReceipt, FabricRoll, CuttingOrder, CuttingCompletion,
    CuttingCompletionSize, StitchingTransfer, StitchingTransferSize,
)
from apps.store.services.production_reconciliation_service import cutting_to_stitching_reconciliation


class ProductionReconciliationTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(username="reconciliation_tester", password="test-password")
        receipt = FabricReceipt.objects.create(
            supplier_name="Example Supplier", dc_number="RECON-1",
            status=FabricReceipt.Status.VERIFIED, created_by=user,
        )
        roll = FabricRoll.objects.create(
            receipt=receipt, supplier_roll_number="438939", fabric_description="Denim",
            received_meters=Decimal("122"), available_meters=Decimal("2"),
            location=FabricRoll.Location.CUTTING,
        )
        order = CuttingOrder.objects.create(
            case_number="635", cutting_master="Master", roll=roll,
            status=CuttingOrder.Status.COMPLETED, created_by=user,
        )
        self.completion = CuttingCompletion.objects.create(
            order=order, consumed_meters=Decimal("119"), waste_meters=Decimal("1"),
            leftover_meters=Decimal("2"), completed_by=user,
        )
        CuttingCompletionSize.objects.create(completion=self.completion, size="32", actual_pieces=105)
        self.user = user

    def transfer(self, reference, issued, received=None):
        transfer = StitchingTransfer.objects.create(
            cutting_completion=self.completion, reference=reference,
            recipient="Stitching Unit", issued_by=self.user,
            status=StitchingTransfer.Status.RECEIVED if received is not None else StitchingTransfer.Status.ISSUED,
        )
        StitchingTransferSize.objects.create(
            transfer=transfer, size="32", issued_pieces=issued, received_pieces=received,
        )
        return transfer

    def test_unissued_pieces_remain_in_cutting(self):
        result = cutting_to_stitching_reconciliation(completion_id=self.completion.pk)
        self.assertEqual(result["totals"]["remaining_in_cutting"], 105)
        self.assertTrue(result["balanced"])

    def test_received_shortage_and_unissued_pieces_are_separate(self):
        self.transfer("T1", 100, received=98)
        result = cutting_to_stitching_reconciliation(completion_id=self.completion.pk)
        self.assertEqual(result["totals"]["remaining_in_cutting"], 5)
        self.assertEqual(result["totals"]["receipt_shortage"], 2)
        self.assertEqual(result["totals"]["received"], 98)
        self.assertTrue(result["balanced"])

    def test_in_transit_is_not_treated_as_shortage(self):
        self.transfer("T1", 50, received=49)
        self.transfer("T2", 50)
        result = cutting_to_stitching_reconciliation(completion_id=self.completion.pk)
        self.assertEqual(result["totals"]["in_transit"], 50)
        self.assertEqual(result["totals"]["receipt_shortage"], 1)
        self.assertTrue(result["balanced"])

    def test_overissued_records_flagged(self):
        self.transfer("T1", 106)
        with self.assertRaises(ValidationError):
            cutting_to_stitching_reconciliation(completion_id=self.completion.pk)
