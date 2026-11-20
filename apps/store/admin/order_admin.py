from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.safestring import mark_safe
from django.core.exceptions import ValidationError

from ..models import Order, OrderItem, Refund
from ..services.order_service import update_order_status
from ..services.refund_service import  calculate_refund_amount


# -----------------------
# ORDER ADMIN
# -----------------------
# Inline admin for order items
class OrderItemInline(admin.TabularInline):

    model = OrderItem

    extra = 0

    readonly_fields = (
        "product",
        "variant",
        "quantity",
        "price",
        "refunded_quantity",
    )

    fields = (
        "product",
        "variant",
        "quantity",
        "price",
        "returned_quantity",
        "refunded_quantity",
    )

def create_shipment_action(modeladmin, request, queryset):

    for order in queryset:

            if order.status != "PACKED":
                messages.error(request, f"Order {order.id} is not PACKED")
                continue

            if order.awb_code:
                messages.error(request, f"Order {order.id} already shipped")
                continue

            try:
                shipment = create_shipment(order)

                order.shipment_id = shipment["shipment_id"]
                order.awb_code = shipment["awb_code"]
                order.courier_name = shipment["courier_name"]
                order.save()

                # USE SERVICE (IMPORTANT)
                update_order_status(order, "SHIPPED")

            except ValidationError as e:
                messages.error(request, f"Order {order.id}: {str(e)}")


#  MARK REFUND PENDING ACTION
def mark_refund_pending(self, request, order_id):

    order = Order.objects.get(id=order_id)

    try:
        update_order_status(order, "REFUND_PENDING")

        # Create refund entry
        existing = Refund.objects.filter(order=order).exists()

        if not existing:
            Refund.objects.create(
                order=order,
                amount=calculate_refund_amount(order),
                status="INITIATED"
            )

        self.message_user(request, "Moved to Refund Pending", messages.SUCCESS)

    except Exception as e:
        self.message_user(request, str(e), messages.ERROR)

    return redirect(request.META.get("HTTP_REFERER"))

# APPROVE REFUND ACTION
def approve_refund(modeladmin, request, queryset):

    for order in queryset:

        try:
            if order.status != "REFUND_PENDING":
                raise ValidationError("Only REFUND_PENDING orders allowed")

            # Check if a refund is already initiated for this order
            existing = Refund.objects.filter(order=order, status__in=["INITIATED", "SUCCESS"]).exists()
            if existing:
                raise ValidationError("Refund already created")

            Refund.objects.create(
                order=order,
                amount=calculate_refund_amount(order),
                status="INITIATED"
            )

            messages.success(request, f"Refund approved for Order {order.id}")

        except ValidationError as e:
            messages.error(request, f"Order {order.id}: {str(e)}")


#def has_add_permission(self, request, obj=None):
#    return request.user.is_superuser


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'customer_name',
        'phone',
        'total_amount',
        'payment_method',
        'status',
        'return_status',
        'action_buttons',
        'created_at'
    )

    readonly_fields = (
        # Customer
        "customer_name",
        "email",
        "phone",
        "address",
        "city",
        "district",
        "pincode",

        # Pricing
        "subtotal",
        "shipping_charge",
        "cod_charge",
        "total_amount",
        "advance_paid_amount",
        "amount_collectable",

        # Payment
        "payment_method",
        "payment_status",
        "razorpay_payment_id",

        # Offers
        "offer_type",
        "offer_title",
        "offer_discount_percentage",
        "offer_discount_amount",
        "exchange_allowed",

        # Dates
        "created_at",
        "paid_at",
        "shipped_at",
        "delivered_at",

        # Status
        "status",
        "return_status",
    )

    fieldsets = (

        (
            "Customer Details",
            {
                "fields": (
                    "customer_name",
                    "email",
                    "phone",
                    "address",
                    "city",
                    "district",
                    "pincode",
                )
            }
        ),

        (
            "Shipping Details",
            {
                "fields": (
                    "provider_name",
                    "courier_name",
                    "awb_code",
                    "tracking_url",
                    "shipment_status",
                )
            }
        ),

        (
            "Pricing",
            {
                "fields": (
                    "subtotal",
                    "shipping_charge",
                    "cod_charge",
                    "total_amount",
                )
            }
        ),

        (
            "Offer Details",
            {
                "fields": (
                    "offer_type",
                    "offer_title",
                    "offer_discount_percentage",
                    "offer_discount_amount",
                    "exchange_allowed",
                )
            }
        ),

        (
            "Order Status",
            {
                "fields": (
                    "status",
                    "payment_method",
                    "payment_status",
                    "paid_at",
                    "shipped_at",
                    "delivered_at",
                )
            }
        ),

    )

    inlines = [OrderItemInline]

    # -----------------------------
    # 🔘 ACTION BUTTONS COLUMN
    # -----------------------------
    def action_buttons(self, obj):

        buttons = ""

        # ONLINE ORDERS

        if obj.status == "PAID":

            buttons += f'<a class="button" href="start-processing/{obj.id}/">▶️ Start</a> '

        # COD ORDERS

        elif (
            obj.payment_method == "COD"
            and obj.status == "CREATED"
        ):

            buttons += f'<a class="button" href="start-processing/{obj.id}/">▶️ Start</a> '

        # PACK
        elif obj.status == "PROCESSING":
            buttons += f'<a class="button" href="pack/{obj.id}/">📦 Pack</a> '

        # SHIP
        elif obj.status == "PACKED":
            buttons += f'<a class="button" href="ship/{obj.id}/">✅ Mark Ready To Ship</a> '
        
        elif obj.status == "READY_TO_SHIP":
            buttons += f'<a class="button" href="mark-shipped/{obj.id}/">🚚 Shipped</a> '

        elif obj.status == "SHIPPED":
            buttons += f'<a class="button" href="out-for-delivery/{obj.id}/">📍 Out For Delivery</a> '

        elif obj.status == "OUT_FOR_DELIVERY":
            buttons += f'<a class="button" href="delivered/{obj.id}/">✅ Delivered</a> '
            buttons += f'<a class="button" href="rto/{obj.id}/">↩️ RTO</a> '

        elif obj.status == "RTO":
            buttons += f'<a class="button" href="return-received/{obj.id}/">Warehouse Received</a> '

        # REFUND FLOW
        elif obj.status == "RETURN_RECEIVED":
            buttons += f'<a class="button" href="refund-pending/{obj.id}/">💸 Refund</a> '

        # CANCEL OPTION
        if obj.status in ["CREATED", "PAID", "PROCESSING", "PACKED"]:
            buttons += f'<a style="background:red;color:white;padding:4px 8px;border-radius:4px;" href="cancel/{obj.id}/">❌ Cancel</a>'

        return mark_safe(buttons or "-")

    action_buttons.short_description = "Actions"

    # -----------------------------
    # 🔗 CUSTOM URLS
    # -----------------------------
    def get_urls(self):
        urls = super().get_urls()

        custom_urls = [
            path("start-processing/<int:order_id>/", self.admin_site.admin_view(self.start_processing)),
            path("pack/<int:order_id>/", self.admin_site.admin_view(self.pack_order)),
            path("mark-shipped/<int:order_id>/",self.admin_site.admin_view(self.mark_shipped)),
            path("out-for-delivery/<int:order_id>/",self.admin_site.admin_view(self.mark_out_for_delivery)),
            path("delivered/<int:order_id>/",self.admin_site.admin_view(self.mark_delivered)),
            path("rto/<int:order_id>/",self.admin_site.admin_view(self.mark_rto)),
            path("ship/<int:order_id>/", self.admin_site.admin_view(self.ship_order)),
            path("return-received/<int:order_id>/", self.admin_site.admin_view(self.mark_return_received),),
            path("refund-pending/<int:order_id>/", self.admin_site.admin_view(self.mark_refund_pending)),
            path("cancel/<int:order_id>/", self.admin_site.admin_view(self.cancel_order)),
        ]

        return custom_urls + urls
    # -----------------------------
    # 📦 PROCESS ORDER
    # -----------------------------
    def start_processing(self, request, order_id):

        order = Order.objects.get(id=order_id)

        try:
            update_order_status(order, "PROCESSING")
            self.message_user(request, "Order moved to PROCESSING", messages.SUCCESS)

        except Exception as e:
            self.message_user(request, str(e), messages.ERROR)

        return redirect(request.META.get("HTTP_REFERER"))
    # -----------------------------
    # 📦 PACK ORDER
    # -----------------------------
    def pack_order(self, request, order_id):

        order = Order.objects.get(id=order_id)

        try:
            update_order_status(order, "PACKED")
            self.message_user(request, "Order Packed", messages.SUCCESS)

        except Exception as e:
            self.message_user(request, str(e), messages.ERROR)

        return redirect(request.META.get("HTTP_REFERER"))

    # -----------------------------
    # 🚚 SHIP ORDER (WITH SHIPMENT)
    # -----------------------------
    def ship_order(self, request, order_id):

        order = Order.objects.get(id=order_id)

        try:
            update_order_status(order, "READY_TO_SHIP")

            self.message_user(
                request,
                "Shipment created. Order moved to READY_TO_SHIP",
                messages.SUCCESS
            )

        except Exception as e:
            self.message_user(request, str(e), messages.ERROR)

        return redirect(request.META.get("HTTP_REFERER"))
    
     # ----------------------------
    # Mark shipped
    # -----------------------------
    def mark_shipped(self, request, order_id):

        order = Order.objects.get(id=order_id)

        try:

            update_order_status(
                order,
                "SHIPPED"
            )

            self.message_user(
                request,
                "Order marked as SHIPPED",
                messages.SUCCESS
            )

        except Exception as e:

            self.message_user(
                request,
                str(e),
                messages.ERROR
            )

        return redirect(
            request.META.get("HTTP_REFERER")
        )
    

    # ----------------------------
    # out for the delivery
    # -----------------------------
    def mark_out_for_delivery(
        self,
        request,
        order_id
    ):

        order = Order.objects.get(
            id=order_id
        )

        try:

            update_order_status(
                order,
                "OUT_FOR_DELIVERY"
            )

            self.message_user(
                request,
                "Order marked as OUT_FOR_DELIVERY",
                messages.SUCCESS
            )

        except Exception as e:

            self.message_user(
                request,
                str(e),
                messages.ERROR
            )

        return redirect(
            request.META.get("HTTP_REFERER")
        )
    
    def mark_delivered(
        self,
        request,
        order_id
    ):

        order = Order.objects.get(
            id=order_id
        )

        try:

            update_order_status(
                order,
                "DELIVERED"
            )

            self.message_user(
                request,
                "Order marked as DELIVERED",
                messages.SUCCESS
            )

        except Exception as e:

            self.message_user(
                request,
                str(e),
                messages.ERROR
            )

        return redirect(
            request.META.get("HTTP_REFERER")
        )
    
    def mark_rto(
        self,
        request,
        order_id
    ):

        order = Order.objects.get(
            id=order_id
        )

        try:

            update_order_status(
                order,
                "RTO"
            )

            self.message_user(
                request,
                "Order marked as RTO",
                messages.SUCCESS
            )

        except Exception as e:

            self.message_user(
                request,
                str(e),
                messages.ERROR
            )

        return redirect(
            request.META.get("HTTP_REFERER")
        )

    # ----------------------------
    # 💸 Mark return received
    # -----------------------------
    def mark_return_received(self, request, order_id):

        order = Order.objects.get(id=order_id)

        try:
            update_order_status(order, "RETURN_RECEIVED")
            self.message_user(request, "Order marked as RETURN_RECEIVED")

        except Exception as e:
            self.message_user(request, str(e), level=messages.ERROR)

        return redirect(request.META.get("HTTP_REFERER"))
    
    # -----------------------------
    # 💸 MOVE TO REFUND PENDING
    # -----------------------------
    def mark_refund_pending(self, request, order_id):

        order = Order.objects.get(id=order_id)

        try:
            # move order status
            update_order_status(order, "REFUND_PENDING")

            # prevent duplicate refund
            existing = Refund.objects.filter(order=order).exists()

            if not existing:

                refund_amount = calculate_refund_amount(order)

                Refund.objects.create(
                    order=order,
                    amount=refund_amount,
                    status="INITIATED"
                )

            self.message_user(request, "Refund initiated successfully")

        except Exception as e:
            self.message_user(request, str(e), level=messages.ERROR)

        return redirect(request.META.get("HTTP_REFERER"))
    
    # -----------------------------
    # 💸 Cancel 
    # -----------------------------

    def cancel_order(self, request, order_id):

        order = Order.objects.get(id=order_id)

        try:
            update_order_status(order, "CANCELLED")
            self.message_user(request, "Order Cancelled", messages.SUCCESS)

        except Exception as e:
            self.message_user(request, str(e), messages.ERROR)

        return redirect(request.META.get("HTTP_REFERER"))