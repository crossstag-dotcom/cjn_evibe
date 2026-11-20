from django.contrib import admin
from django.template.response import TemplateResponse

from apps.store.services.analytics_service import (
    get_revenue_today,
    get_orders_today,
    get_pending_orders,
    get_in_transit_orders,
    get_returns_count,
    get_refunds_total,
    get_top_products,
    get_low_stock_products,
    get_orders_trend,
    get_order_status_distribution,
    get_revenue_trend,
    get_product_views_trend
)

from apps.analytics.models import AnalyticsDashboard



# ----------------------------------
# ANALYTICS DASHBOARD
# ----------------------------------
class AnalyticsAdmin(admin.ModelAdmin):

    change_list_template = "admin/analytics_dashboard.html"

    def changelist_view(self, request, extra_context=None):

        # Safely parse and limit reporting periods.
        try:
            days = int(request.GET.get("days", 7))
        except (TypeError, ValueError):
            days = 7
        days = max(1, min(days, 90))

        labels, values = get_orders_trend(days)
        status_labels, status_values = get_order_status_distribution()
        revenue_labels, revenue_values = get_revenue_trend(days)
        
        view_labels, view_values = get_product_views_trend(days)

        context = {
            "revenue_today": get_revenue_today(),
            "orders_today": get_orders_today(),
            "pending_orders": get_pending_orders(),
            "in_transit_orders": get_in_transit_orders(),
            "returns_count": get_returns_count(),
            "refunds_total": get_refunds_total(),
            "top_products": get_top_products(),
            "low_stock_products": get_low_stock_products(),

            "chart_labels": labels,
            "chart_values": values,
            "status_labels": status_labels,
            "status_values": status_values,
            "revenue_labels": revenue_labels,
            "revenue_values": revenue_values,
            "view_labels": view_labels,
            "view_values": view_values,
            "days": days
        }

        return TemplateResponse(
            request,
            "admin/analytics_dashboard.html",
            context
        )


admin.site.register(AnalyticsDashboard, AnalyticsAdmin)