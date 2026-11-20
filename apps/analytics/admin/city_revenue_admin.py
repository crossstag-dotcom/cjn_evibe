from django.contrib import admin
from django.template.response import TemplateResponse

from apps.store.services.analytics_service import (
    get_city_wise_revenue_intelligence
)
from apps.analytics.models import CityRevenueIntelligence


class CityRevenueIntelligenceAdmin(admin.ModelAdmin):

    change_list_template = "admin/city_revenue_intelligence.html"

    def changelist_view(self, request, extra_context=None):

        days = request.GET.get("days", 30)

        if days == "all":
            selected_days = "All Time"
        else:
            selected_days = f"Last {days} Days"

        context = {
            "city_data": get_city_wise_revenue_intelligence(days),
            "selected_days": selected_days,
            "days": days
        }

        return TemplateResponse(
            request,
            "admin/city_revenue_intelligence.html",
            context
        )


admin.site.register(
    CityRevenueIntelligence,
    CityRevenueIntelligenceAdmin
)