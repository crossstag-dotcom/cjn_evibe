"""Isolated API routes: does not replace existing storefront or dashboard URLs."""
from django.urls import path
from apps.store.views.manufacturing_api import cutting_stitching_reconciliation_api, manufacturing_summary_api, pending_stitching_transfers_api, variant_inventory_reconciliation_api

urlpatterns = [
    path('inventory/variants/<int:variant_id>/reconciliation/', variant_inventory_reconciliation_api, name='manufacturing_variant_stock_reconciliation_api'),
    path('stitching/pending/', pending_stitching_transfers_api, name='manufacturing_pending_stitching_transfers_api'),
    path('summary/', manufacturing_summary_api, name='manufacturing_summary_api'),
    path(
        "cutting-completions/<int:completion_id>/reconciliation/",
        cutting_stitching_reconciliation_api,
        name="manufacturing_cutting_stitching_reconciliation",
    ),
]
