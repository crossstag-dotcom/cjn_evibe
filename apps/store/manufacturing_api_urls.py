"""Isolated API routes: does not replace existing storefront or dashboard URLs."""
from django.urls import path
from apps.store.views.manufacturing_api import cutting_stitching_reconciliation_api, manufacturing_summary_api, pending_stitching_transfers_api

urlpatterns = [
    path('stitching/pending/', pending_stitching_transfers_api, name='manufacturing_pending_stitching_transfers_api'),
    path('summary/', manufacturing_summary_api, name='manufacturing_summary_api'),
    path(
        "cutting-completions/<int:completion_id>/reconciliation/",
        cutting_stitching_reconciliation_api,
        name="manufacturing_cutting_stitching_reconciliation",
    ),
]
