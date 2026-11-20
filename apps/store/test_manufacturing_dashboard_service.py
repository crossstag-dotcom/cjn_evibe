from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase

from apps.store.services.manufacturing_dashboard_service import get_manufacturing_summary


class ManufacturingDashboardSummaryTests(TestCase):
    def test_empty_database_has_zero_work_in_progress(self):
        summary = get_manufacturing_summary()
        self.assertEqual(summary["cut_pieces"], 0)
        self.assertEqual(summary["received_at_stitching"], 0)
        self.assertEqual(summary["receipt_shortage"], 0)
        self.assertTrue(summary["reconciliation_ok"])

    @patch("apps.store.admin.analytics_admin.get_manufacturing_summary")
    def test_existing_admin_dashboard_does_not_query_manufacturing_without_permission(self, summary):
        from apps.store.admin.analytics_admin import AnalyticsAdmin
        from apps.analytics.models import AnalyticsDashboard
        from django.contrib import admin
        from django.test import RequestFactory
        user = get_user_model().objects.create_user(username="limited_staff", is_staff=True)
        user.user_permissions.add(
            Permission.objects.get(content_type__app_label="analytics", codename="view_analyticsdashboard")
        )
        request = RequestFactory().get("/admin/")
        request.user = user
        dashboard = AnalyticsAdmin(AnalyticsDashboard, admin.site)
        with patch.object(dashboard, "has_view_or_change_permission", return_value=True), \
             patch("apps.store.admin.analytics_admin.get_orders_trend", return_value=([], [])), \
             patch("apps.store.admin.analytics_admin.get_order_status_distribution", return_value=([], [])), \
             patch("apps.store.admin.analytics_admin.get_revenue_trend", return_value=([], [])), \
             patch("apps.store.admin.analytics_admin.get_product_views_trend", return_value=([], [])):
            response = dashboard.changelist_view(request)
        self.assertIsNone(response.context_data["manufacturing_summary"])
        summary.assert_not_called()
