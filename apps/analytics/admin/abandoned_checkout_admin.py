from django.contrib import admin
from django.template.response import TemplateResponse

from apps.store.services.analytics_service import get_abandoned_checkouts
from apps.analytics.models import AbandonedCheckout


class AbandonedCheckoutAdmin(admin.ModelAdmin):

    change_list_template = "admin/abandoned_checkout.html"

    def changelist_view(self, request, extra_context=None):

        context = {
            "abandoned_data": get_abandoned_checkouts()
        }

        return TemplateResponse(
            request,
            "admin/abandoned_checkout.html",
            context
        )


admin.site.register(AbandonedCheckout, AbandonedCheckoutAdmin)