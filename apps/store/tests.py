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
