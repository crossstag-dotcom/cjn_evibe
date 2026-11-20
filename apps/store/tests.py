"""Regression tests for the EVIBE executive dashboard."""
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class ExecutiveDashboardTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_user = get_user_model().objects.create_superuser(
            username="dashboard-test-admin",
            email="dashboard-test@example.invalid",
            password="test-password-not-for-production",
        )

    def setUp(self):
        self.client.force_login(self.admin_user)
        self.url = reverse("admin:analytics_analyticsdashboard_changelist")

    def test_reporting_period_rejects_invalid_and_out_of_range_values(self):
        with (
            patch("apps.store.admin.analytics_admin.get_orders_trend", return_value=([], [])) as orders,
            patch("apps.store.admin.analytics_admin.get_order_status_distribution", return_value=([], [])),
            patch("apps.store.admin.analytics_admin.get_revenue_trend", return_value=([], [])),
            patch("apps.store.admin.analytics_admin.get_product_views_trend", return_value=([], [])),
            patch("apps.store.admin.analytics_admin.get_revenue_today", return_value=0),
            patch("apps.store.admin.analytics_admin.get_orders_today", return_value=0),
            patch("apps.store.admin.analytics_admin.get_pending_orders", return_value=0),
            patch("apps.store.admin.analytics_admin.get_in_transit_orders", return_value=0),
            patch("apps.store.admin.analytics_admin.get_returns_count", return_value=0),
            patch("apps.store.admin.analytics_admin.get_refunds_total", return_value=0),
            patch("apps.store.admin.analytics_admin.get_top_products", return_value=[]),
            patch("apps.store.admin.analytics_admin.get_low_stock_products", return_value=[]),
        ):
            for supplied, expected in (("invalid", 7), ("0", 1), ("999", 90), ("30", 30)):
                with self.subTest(supplied=supplied):
                    response = self.client.get(self.url, {"days": supplied})
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.context_data["days"], expected)
                    orders.assert_called_with(expected)

    def test_anonymous_user_cannot_access_dashboard(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response["Location"])


class WarehouseLedgerTests(TestCase):
    """Run after creating and applying the inventory model migrations."""

    @classmethod
    def setUpTestData(cls):
        from decimal import Decimal
        from apps.store.models import Product, ProductVariant, Warehouse
        cls.user = get_user_model().objects.create_superuser(
            username="ledger-test-admin", email="ledger-test@example.invalid",
            password="test-password-not-for-production"
        )
        product = Product.objects.create(
            product_code="LEDGER-TEST", name="Ledger test trouser",
            cost_price=Decimal("100.00"), mrp=Decimal("200.00"),
            price=Decimal("150.00"),
        )
        cls.variant = ProductVariant.objects.create(product=product, size="32", stock=0)
        cls.source = Warehouse.objects.create(code="TEST-MAIN", name="Test Main")
        cls.destination = Warehouse.objects.create(code="TEST-B", name="Test B")

    def test_transfer_preserves_total_and_records_both_sides(self):
        from apps.store.models import InventoryBalance, StockMovement
        from apps.store.services.inventory_service import post_stock_movement, transfer_stock
        post_stock_movement(
            variant=self.variant, warehouse=self.source, delta=50,
            reason=StockMovement.Reason.RECEIPT, reference="GRN-TEST-1", user=self.user
        )
        transfer_stock(
            variant=self.variant, source=self.source, destination=self.destination,
            quantity=20, reference="TRF-TEST-1", user=self.user
        )
        self.assertEqual(InventoryBalance.objects.get(variant=self.variant, warehouse=self.source).quantity, 30)
        self.assertEqual(InventoryBalance.objects.get(variant=self.variant, warehouse=self.destination).quantity, 20)
        self.assertEqual(StockMovement.objects.filter(reference="TRF-TEST-1").count(), 2)

    def test_insufficient_stock_does_not_create_movement(self):
        from django.core.exceptions import ValidationError
        from apps.store.models import StockMovement
        from apps.store.services.inventory_service import post_stock_movement
        with self.assertRaises(ValidationError):
            post_stock_movement(
                variant=self.variant, warehouse=self.source, delta=-1,
                reason=StockMovement.Reason.ISSUE, reference="ISS-TEST-1", user=self.user
            )
        self.assertFalse(StockMovement.objects.filter(reference="ISS-TEST-1").exists())

    def test_duplicate_reference_is_rejected(self):
        from django.core.exceptions import ValidationError
        from apps.store.models import StockMovement
        from apps.store.services.inventory_service import post_stock_movement
        args = dict(
            variant=self.variant, warehouse=self.source, delta=5,
            reason=StockMovement.Reason.RECEIPT, reference="GRN-TEST-DUP", user=self.user
        )
        post_stock_movement(**args)
        with self.assertRaises(ValidationError):
            post_stock_movement(**args)
