from django.contrib import admin

from ..models import StoreConfiguration


@admin.register(StoreConfiguration)
class StoreConfigurationAdmin(admin.ModelAdmin):

    list_display = (
        "shipping_per_pant",
        "cod_charge",
        "cod_enabled",
        "max_cod_order_value",
        "return_window_days",
        "updated_at",
    )

    def has_add_permission(self, request):

        return not StoreConfiguration.objects.exists()