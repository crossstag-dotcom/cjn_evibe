"""Read-only reconciliation API contract and permission checks."""
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse


class VariantReconciliationApiTests(TestCase):
    def setUp(self):
        self.url = reverse("manufacturing_variant_stock_reconciliation_api", args=[42])
        self.user = get_user_model().objects.create_user(
            username="stock_reconciliation_viewer", password="test-password"
        )

    def grant_view_permission(self):
        self.user.user_permissions.add(Permission.objects.get(
            content_type__app_label="store", codename="view_inventorybalance"
        ))

    def test_anonymous_redirects_to_existing_login(self):
        self.assertEqual(self.client.get(self.url).status_code, 302)

    def test_user_without_permission_is_forbidden(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    @patch("apps.store.views.manufacturing_api.get_variant_stock_reconciliation")
    def test_authorized_reconciliation_is_read_only(self, service):
        self.grant_view_permission()
        self.client.force_login(self.user)
        service.return_value = {
            "variant_id": 42, "warehouse_quantity": 300,
            "storefront_quantity": 285, "difference": 15,
            "automatic_sync_enabled": False, "sync_mode": "READ_ONLY",
        }
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["schema_version"], 1)
        self.assertEqual(response.json()["reconciliation"]["difference"], 15)
        self.assertFalse(response.json()["reconciliation"]["automatic_sync_enabled"])
        self.assertEqual(response["Cache-Control"], "no-store")
        service.assert_called_once_with(variant_id=42)

    def test_post_cannot_change_stock(self):
        self.grant_view_permission()
        self.client.force_login(self.user)
        self.assertEqual(self.client.post(self.url).status_code, 405)
