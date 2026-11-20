from django.contrib import admin
from ..models import ReturnRequest

@admin.register(ReturnRequest)
class ReturnRequestAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'order',
        'order_item',
        'quantity',
        'reason',
        'preferred_pickup_date',
        'status',
        'created_at'
    )

    list_filter = ('status',)
    search_fields = ('order__id',)
    fieldsets = (

        (
            "Return Details",
            {
                "fields": (
                    "order",
                    "order_item",
                    "quantity",
                    "status",
                )
            }
        ),

        (
            "Customer Request",
            {
                "fields": (
                    "reason",
                    "customer_comments",
                    "preferred_pickup_date",
                )
            }
        ),

        (
            "Inspection",
            {
                "fields": (
                    "inspection_notes",
                )
            }
        ),

    )

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ('order', 'order_item', 'quantity', 'reason', 'customer_comments', 'preferred_pickup_date')
        return ()
    
    class Media:
        js = ("admin/js/return_request.js",)