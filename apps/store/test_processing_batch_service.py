"""Regression checks for washing/processing custody; no finished-goods posting."""
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.store.models import ProcessingBatch, ProcessingBatchSize, StitchingTransfer
from apps.store.services.processing_batch_service import issue_processing_batch, confirm_processing_receipt


class ProcessingBatchServiceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="processing_operator", password="test-password")
        self.user.user_permissions.add(*Permission.objects.filter(
            content_type__app_label="store",
            codename__in=["add_processingbatch", "change_processingbatch"],
        ))

    def test_unreceived_stitching_cannot_enter_processing(self):
        with self.assertRaises(StitchingTransfer.DoesNotExist):
            issue_processing_batch(
                stitching_transfer_id=999999, reference="PROC-1",
                processor="Wash House", user=self.user,
            )

    def test_receipt_rejects_missing_batch(self):
        with self.assertRaises(ProcessingBatch.DoesNotExist):
            confirm_processing_receipt(batch_id=999999, received_sizes={"32": 10}, user=self.user)

    def test_no_mutation_when_invalid_receipt(self):
        with self.assertRaises(ProcessingBatch.DoesNotExist):
            confirm_processing_receipt(batch_id=999999, received_sizes={"32": -1}, user=self.user)
