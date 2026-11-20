from django.contrib import admin
from django.template.response import TemplateResponse

from apps.store.services.analytics_service import get_dead_products
from apps.analytics.models import DeadProductsReport


class DeadProductsReportAdmin(admin.ModelAdmin):

    change_list_template = "admin/dead_products.html"

    def changelist_view(self, request, extra_context=None):

        context = {
            "dead_products": get_dead_products()
        }

        return TemplateResponse(
            request,
            "admin/dead_products.html",
            context
        )


admin.site.register(
    DeadProductsReport,
    DeadProductsReportAdmin
)