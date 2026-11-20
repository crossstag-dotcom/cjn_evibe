from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.html import format_html

from ..models import Refund
from ..services.refund_service import process_refund, calculate_refund_amount    


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'amount', 'colored_status','approved_by','approve_button', 'created_at')
    readonly_fields = ('order','razorpay_refund_id', 'status', 'created_at')
    search_fields = ('order__id',)
    list_filter = ('status',)

    def colored_status(self, obj):

        if obj.status == "SUCCESS":
            color = "green"
        elif obj.status == "FAILED":
            color = "red"
        else:
            color = "orange"

        return format_html(
            '<span style="color:white;padding:4px 8px;border-radius:6px;background-color:{};">{}</span>',
            color,
            obj.status
        )
    
    # -------------------
    # BUTTON COLUMN
    # -------------------
    def approve_button(self, obj):

        if obj.status == "INITIATED":
            return format_html(
                '<a style="background-color:#28a745;color:white;padding:6px 12px;border-radius:6px;text-decoration:none;" href="approve-refund/{}/">{}</a>',
                obj.id,
                "Approve"
            )

        elif obj.status == "FAILED":
            return format_html(
                '<a style="background-color:#ffc107;color:black;padding:6px 12px;border-radius:6px;text-decoration:none;" href="approve-refund/{}/">{}</a>',
                obj.id,
                "Retry"
            )

        return format_html(
            '<span style="color:green;font-weight:bold;">{}</span>',
            "✔ Refunded"
        )

    # -------------------
    # CUSTOM URL
    # -------------------
    def get_urls(self):
        urls = super().get_urls()

        custom_urls = [
            path(
                'approve-refund/<int:refund_id>/',
                self.admin_site.admin_view(self.process_refund_view),
            ),
        ]

        return custom_urls + urls

    # -------------------
    # BUTTON ACTION LOGIC
    # -------------------
    def process_refund_view(self, request, refund_id):

        if not request.user.is_superuser:
            self.message_user(request, "Only admin can approve refund", level=messages.ERROR)
            return redirect(request.META.get('HTTP_REFERER'))

        refund = Refund.objects.get(id=refund_id)

        try:
            if refund.status not in ["INITIATED", "FAILED"]:
                self.message_user(request, "Already processed", level=messages.ERROR)
                return redirect(request.META.get('HTTP_REFERER'))

            result = process_refund(refund.order, refund, None)

            refund.refresh_from_db()

            if result.status == "SUCCESS":

                refund.approved_by = request.user
                refund.save()

                # Optional: show how much refund still pending
                remaining = calculate_refund_amount(refund.order)

                if remaining > 0:
                    self.message_user(
                        request,
                        f"Refund SUCCESS. Remaining refundable amount: ₹{remaining}",
                        level=messages.SUCCESS
                    )
                else:
                    self.message_user(request, "Refund SUCCESS. All items refunded.", level=messages.SUCCESS)

            else:
                self.message_user(request, "Refund FAILED", level=messages.ERROR)

        except Exception as e:
            self.message_user(request, str(e), level=messages.ERROR)

        return redirect(request.META.get('HTTP_REFERER'))

class Media:
    js = ("admin/js/return_request.js",)