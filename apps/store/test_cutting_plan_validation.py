from decimal import Decimal
from django.test import SimpleTestCase
from apps.store.services.cutting_plan_validation import (
    CuttingPlanError, summarize_cutting_plan,
)


class CuttingPlanValidationTests(SimpleTestCase):
    def test_cutting_dc_example(self):
        result = summarize_cutting_plan(
            {"28": 21, "30": 21, "32": 21, "34": 21, "36": 21},
            "1.16", "122",
        )
        self.assertEqual(result["planned_pieces"], 105)
        self.assertEqual(result["estimated_meters"], Decimal("121.80"))
        self.assertEqual(result["estimated_difference_meters"], Decimal("0.20"))
        self.assertFalse(result["estimated_exceeds_roll"])

    def test_estimate_over_roll_is_flagged(self):
        result = summarize_cutting_plan({"32": 105}, "1.20", "122")
        self.assertTrue(result["estimated_exceeds_roll"])

    def test_invalid_quantities_are_rejected(self):
        for sizes in ({}, {"32": 0}, {"32": -1}, {"32": 2.5}, {"32": True}):
            with self.subTest(sizes=sizes), self.assertRaises(CuttingPlanError):
                summarize_cutting_plan(sizes, "1.16", "122")

    def test_invalid_average_is_rejected(self):
        for average in ("NaN", "Infinity", "0", "-1", "invalid"):
            with self.subTest(average=average), self.assertRaises(CuttingPlanError):
                summarize_cutting_plan({"32": 1}, average, "122")
