from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.db.models import Sum
from django.utils import timezone

from apps.store.models import Order


@staff_member_required
def analytics_dashboard(request):

    today = timezone.now().date()

    revenue_today = (
        Order.objects.filter(
            created_at__date=today,
            status="DELIVERED"
        ).aggregate(total=Sum("total_amount"))["total"] or 0
    )

    orders_today = Order.objects.filter(
        created_at__date=today
    ).count()

    pending_orders = Order.objects.filter(
        status="PROCESSING"
    ).count()

    context = {
        "revenue_today": revenue_today,
        "orders_today": orders_today,
        "pending_orders": pending_orders,
    }

    return render(request, "admin/analytics_dashboard.html", context)