from django.contrib import admin
from django.template.response import TemplateResponse

from apps.store.services.analytics_service import get_views_vs_orders
from apps.analytics.models import ViewsVsOrders


class ViewsVsOrdersAdmin(admin.ModelAdmin):

    change_list_template = "admin/views_vs_orders.html"

    def changelist_view(self, request, extra_context=None):

        context = {
            "comparison_data": get_views_vs_orders()
        }

        return TemplateResponse(
            request,
            "admin/views_vs_orders.html",
            context
        )


admin.site.register(ViewsVsOrders, ViewsVsOrdersAdmin)