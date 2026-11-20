"""Access and contract tests for read-only pending stitching transfers."""
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse


class PendingStitchingTransfersApiTests(TestCase):
    def setUp(self):
        self.url = reverse("manufacturing_pending_stitching_transfers_api")
        self.user = get_user_model().objects.create_user(
            username="stitching_monitor_viewer", password="test-password"
        )

    def grant_permission(self):
        self.user.user_permissions.add(Permission.objects.get(
            content_type__app_label="store", codename="view_stitchingtransfer"
        ))

    def test_anonymous_redirects_to_existing_login(self):
        self.assertEqual(self.client.get(self.url).status_code, 302)

    def test_missing_permission_is_forbidden(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    @patch("apps.store.views.manufacturing_api.get_pending_stitching_transfers")
    def test_authorized_user_receives_versioned_read_only_contract(self, service):
        self.grant_permission()
        self.client.force_login(self.user)
        service.return_value = [{
            "transfer_id": 3, "reference": "ST-003", "cutting_case": "635",
            "sizes": {"32": 21}, "total_issued_pieces": 21,
        }]
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["schema_version"], 1)
        self.assertEqual(response.json()["pending_transfers"][0]["total_issued_pieces"], 21)
        self.assertEqual(response["Cache-Control"], "no-store")
        service.assert_called_once_with(limit=100)

    def test_invalid_limit_is_rejected(self):
        self.grant_permission()
        self.client.force_login(self.user)
        response = self.client.get(self.url, {"limit": "201"})
        self.assertEqual(response.status_code, 400)

    def test_post_is_not_allowed(self):
        self.grant_permission()
        self.client.force_login(self.user)
        self.assertEqual(self.client.post(self.url).status_code, 405)
