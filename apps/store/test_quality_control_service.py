"""QC posting invariants and permission regression tests."""
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import SimpleTestCase

from apps.store.services.quality_control_service import post_quality_inspection


class QualityControlValidationTests(SimpleTestCase):
    def test_permission_is_required_before_database_access(self):
        with self.assertRaises(PermissionDenied):
            post_quality_inspection(
                processing_batch_id=1, reference="QC-1",
                results={"32": {"inspected": 1, "approved": 1, "rework": 0, "rejected": 0}},
                user=None,
            )

    def test_invalid_reference_rejected_before_database_access(self):
        class AllowedUser:
            is_authenticated = True
            def has_perm(self, permission):
                return permission == "store.add_qualityinspection"

        with self.assertRaises(ValidationError):
            post_quality_inspection(
                processing_batch_id=1, reference="",
                results={"32": {"inspected": 1, "approved": 1, "rework": 0, "rejected": 0}},
                user=AllowedUser(),
            )

    def test_empty_size_results_rejected_before_database_access(self):
        class AllowedUser:
            is_authenticated = True
            def has_perm(self, permission):
                return True

        with self.assertRaises(ValidationError):
            post_quality_inspection(
                processing_batch_id=1, reference="QC-1",
                results={}, user=AllowedUser(),
            )
