from django.contrib import admin
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html

from apps.analytics.models import ProductView


class ProductViewSummaryAdmin(admin.ModelAdmin):

    change_list_template = "admin/product_view_summary.html"

    def changelist_view(self, request, extra_context=None):

        data = (
            ProductView.objects
            .values("product__id", "product__name")
            .annotate(total_views=Count("id"))
            .order_by("-total_views")
        )

        context = {
            "summary_data": data
        }

        return super().changelist_view(
            request,
            extra_context=context
        )