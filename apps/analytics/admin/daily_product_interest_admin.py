from django.contrib import admin
from django.template.response import TemplateResponse

from apps.store.services.analytics_service import (
    get_daily_product_interest,
    get_product_drilldown
)

from apps.analytics.models import ProductView


class DailyProductInterestAdmin(admin.ModelAdmin):

    change_list_template = "admin/daily_product_interest.html"

    def changelist_view(self, request, extra_context=None):

        product_id = request.GET.get("product_id")
        selected_date = request.GET.get("date")

        # If product clicked → show drilldown
        if product_id and selected_date:

            context = get_product_drilldown(
                product_id=product_id,
                selected_date=selected_date
            )

            return TemplateResponse(
                request,
                "admin/product_drilldown.html",
                context
            )

        # Default → show daily product interest
        context = {
            "grouped_data": get_daily_product_interest()
        }

        return TemplateResponse(
            request,
            "admin/daily_product_interest.html",
            context
        )


admin.site.register(ProductView, DailyProductInterestAdmin)