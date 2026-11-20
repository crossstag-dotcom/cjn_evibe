"""Authenticated read-only manufacturing reconciliation endpoint."""
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from apps.store.models import CuttingCompletion
from apps.store.services.manufacturing_dashboard_service import get_manufacturing_summary
from apps.store.services.production_reconciliation_service import cutting_to_stitching_reconciliation


@login_required
@permission_required("store.view_cuttingcompletion", raise_exception=True)
@require_GET
def cutting_stitching_reconciliation_api(request, completion_id):
    try:
        data = cutting_to_stitching_reconciliation(completion_id=completion_id)
    except CuttingCompletion.DoesNotExist:
        return JsonResponse({"error": "Cutting completion not found."}, status=404)
    except ValidationError as exc:
        return JsonResponse({"error": exc.messages}, status=409)
    response = JsonResponse(data)
    response["Cache-Control"] = "no-store"
    return response


@login_required
@permission_required("store.view_cuttingcompletion", raise_exception=True)
@require_GET
def manufacturing_summary_api(request):
    """Shared JSON contract for web dashboard and authenticated mobile clients."""
    response = JsonResponse({"schema_version": 1, "summary": get_manufacturing_summary()})
    response["Cache-Control"] = "no-store"
    return response
