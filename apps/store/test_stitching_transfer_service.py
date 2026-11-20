from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.store.models import (
    FabricReceipt, FabricRoll, CuttingOrder, CuttingCompletion,
    CuttingCompletionSize, StitchingTransfer, StitchingTransferSize,
)
from apps.store.services.stitching_transfer_service import issue_cut_pieces_to_stitching


class StitchingTransferTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="stitching_tester", password="test-password"
        )
        self.user.user_permissions.add(Permission.objects.get(codename="add_stitchingtransfer"))
        receipt = FabricReceipt.objects.create(
            supplier_name="Test Supplier", dc_number="STITCH-DC",
            status=FabricReceipt.Status.VERIFIED, created_by=self.user,
        )
        roll = FabricRoll.objects.create(
            receipt=receipt, supplier_roll_number="438939",
            fabric_description="Denim", received_meters=Decimal("122"),
            available_meters=Decimal("2"), location=FabricRoll.Location.CUTTING,
        )
        order = CuttingOrder.objects.create(
            case_number="635", cutting_master="Master", roll=roll,
            status=CuttingOrder.Status.COMPLETED, created_by=self.user,
        )
        self.completion = CuttingCompletion.objects.create(
            order=order, consumed_meters=Decimal("119"),
            waste_meters=Decimal("1"), leftover_meters=Decimal("2"),
            completed_by=self.user,
        )
        for size in ("28", "30", "32", "34", "36"):
            CuttingCompletionSize.objects.create(
                completion=self.completion, size=size, actual_pieces=21,
            )

    def issue(self, reference, sizes):
        return issue_cut_pieces_to_stitching(
            completion_id=self.completion.pk, reference=reference,
            recipient="Stitching Unit A", sizes=sizes, user=self.user,
        )

    def test_two_partial_transfers_balance_exactly(self):
        first = self.issue("ST-1", {"28": 10, "30": 21})
        second = self.issue("ST-2", {"28": 11, "32": 21, "34": 21, "36": 21})
        self.assertEqual(first.size_lines.count(), 2)
        self.assertEqual(second.size_lines.count(), 4)
        self.assertEqual(
            sum(StitchingTransferSize.objects.values_list("issued_pieces", flat=True)), 105
        )

    def test_overissue_is_rejected_without_creating_transfer(self):
        self.issue("ST-1", {"28": 20})
        with self.assertRaises(ValidationError):
            self.issue("ST-2", {"28": 2})
        self.assertEqual(StitchingTransfer.objects.count(), 1)

    def test_duplicate_reference_is_rejected(self):
        self.issue("ST-1", {"28": 1})
        with self.assertRaises(ValidationError):
            self.issue("ST-1", {"30": 1})

    def test_unrecorded_size_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.issue("ST-1", {"40": 1})
