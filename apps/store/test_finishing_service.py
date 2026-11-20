"""Basic guardrail tests for finishing and QC rework operations."""
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import SimpleTestCase

from apps.store.services.finishing_service import (
    complete_finishing_batch, mark_rework_repaired,
    open_finishing_batch, open_qc_rework_ticket,
)


class AllowedUser:
    is_authenticated = True

    def has_perm(self, permission):
        return True


class FinishingGuardrailTests(SimpleTestCase):
    def test_anonymous_cannot_open_finishing(self):
        with self.assertRaises(PermissionDenied):
            open_finishing_batch(inspection_id=1, reference="FIN-1", user=None)

    def test_invalid_reference_rejected_before_database_access(self):
        with self.assertRaises(ValidationError):
            open_finishing_batch(inspection_id=1, reference="", user=AllowedUser())

    def test_anonymous_cannot_complete_finishing(self):
        with self.assertRaises(PermissionDenied):
            complete_finishing_batch(batch_id=1, results={}, user=None)

    def test_rework_requires_positive_pieces(self):
        with self.assertRaises(ValidationError):
            open_qc_rework_ticket(
                inspection_id=1, reference="RW-1", size="32",
                pieces=0, reason="Measurement defect", user=AllowedUser(),
            )

    def test_repair_status_requires_permission(self):
        with self.assertRaises(PermissionDenied):
            mark_rework_repaired(ticket_id=1, user=None)
