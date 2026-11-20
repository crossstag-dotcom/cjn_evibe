from django.contrib import admin
from .models import EmailOTP

from .models import (
    CustomerLead,
    RewardCoupon
)



@admin.register(CustomerLead)
class CustomerLeadAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'email',
        'mobile',
        'login_provider',
        'preferred_style',
        'city',
        'created_at',
    )

    search_fields = (
        'email',
        'mobile',
        'session_id',
    )

    list_filter = (
        'login_provider',
        'preferred_style',
        'created_at',
    )


@admin.register(RewardCoupon)
class RewardCouponAdmin(admin.ModelAdmin):

    list_display = (
        'coupon_code',
        'customer',
        'discount_percentage',
        'is_used',
        'valid_till',
    )

    search_fields = (
        'coupon_code',
    )

    list_filter = (
        'is_used',
    )

@admin.register(EmailOTP)
class EmailOTPAdmin(admin.ModelAdmin):

    list_display = (
        'email',
        'otp',
        'is_verified',
        'expires_at',
        'created_at',
    )

    search_fields = (
        'email',
    )


