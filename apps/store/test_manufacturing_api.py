"""Contract and access-control tests; no production stock is modified."""
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse


class ManufacturingReconciliationApiTests(TestCase):
    def setUp(self):
        self.url = reverse("manufacturing_cutting_stitching_reconciliation", args=[42])
        self.user = get_user_model().objects.create_user(
            username="manufacturing_viewer", password="test-password"
        )

    def test_anonymous_user_must_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_user_without_view_permission_is_denied(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    @patch("apps.store.views.manufacturing_api.cutting_to_stitching_reconciliation")
    def test_authorized_viewer_receives_read_only_data(self, service):
        permission = Permission.objects.get(
            content_type__app_label="store", codename="view_cuttingcompletion"
        )
        self.user.user_permissions.add(permission)
        self.client.force_login(self.user)
        service.return_value = {
            "cutting_case": "635", "sizes": {"32": {"cut": 105}},
            "totals": {"cut": 105}, "balanced": True,
        }
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["totals"]["cut"], 105)
        self.assertEqual(response["Cache-Control"], "no-store")
        service.assert_called_once_with(completion_id=42)

    def test_post_is_not_allowed(self):
        permission = Permission.objects.get(
            content_type__app_label="store", codename="view_cuttingcompletion"
        )
        self.user.user_permissions.add(permission)
        self.client.force_login(self.user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 405)
