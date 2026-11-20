from decimal import Decimal
from django.test import SimpleTestCase
from apps.store.services.fabric_receipt_validation import (
    FabricReceiptError, normalize_roll_number, validate_dc_rolls,
)


class FabricReceiptValidationTests(SimpleTestCase):
    def test_bafna_example_reconciles_to_1080_meters(self):
        rolls = [
            *[{"fabric_code": "4295 Fresh", "roll_number": f"A{i}", "meters": m}
              for i, m in enumerate([100, 113, 100, 115, 115], 1)],
            *[{"fabric_code": "1014 Fresh", "roll_number": f"B{i}", "meters": m}
              for i, m in enumerate([100, 91, 79, 90, 91, 86], 1)],
        ]
        summary = validate_dc_rolls(rolls)
        self.assertEqual(summary["roll_count"], 11)
        self.assertEqual(summary["total_meters"], Decimal("1080"))
        self.assertEqual(summary["fabrics"]["4295 Fresh"]["meters"], Decimal("543"))
        self.assertEqual(summary["fabrics"]["1014 Fresh"]["meters"], Decimal("537"))

    def test_preserves_leading_zeroes(self):
        self.assertEqual(normalize_roll_number("0010250"), "0010250")

    def test_rejects_duplicate_roll_number(self):
        with self.assertRaises(FabricReceiptError):
            validate_dc_rolls([
                {"fabric_code": "A", "roll_number": "0001", "meters": "20"},
                {"fabric_code": "B", "roll_number": "0001", "meters": "30"},
            ])

    def test_rejects_nonpositive_and_invalid_meters(self):
        for value in ("0", "-2", "NaN", "not a number"):
            with self.subTest(value=value), self.assertRaises(FabricReceiptError):
                validate_dc_rolls([{"fabric_code": "A", "roll_number": "1", "meters": value}])
