from django.db import models
from django.utils import timezone
import uuid


# ===============================
# CUSTOMER LEAD
# ===============================

class CustomerLead(models.Model):

    LOGIN_PROVIDER_CHOICES = [
        ('google', 'Google'),
        ('mobile', 'Mobile'),
        ('guest', 'Guest'),
    ]

    STYLE_CHOICES = [
        ('baggy','Baggy'),
        ('lenin','Lenin'),
        ('denim','Denim'),
    ]

    lead_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )

    name = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    email = models.EmailField(
        blank=True,
        null=True,
        unique=True
    )

    mobile = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    login_provider = models.CharField(
        max_length=20,
        choices=LOGIN_PROVIDER_CHOICES,
        default='guest'
    )

    preferred_style = models.CharField(
        max_length=20,
        choices=STYLE_CHOICES,
        blank=True,
        null=True
    )

    session_id = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    city = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.email or self.mobile or self.lead_id}"


# ===============================
# REWARD COUPON
# ===============================

class RewardCoupon(models.Model):

    coupon_code = models.CharField(
        max_length=50,
        unique=True
    )

    customer = models.ForeignKey(
        CustomerLead,
        on_delete=models.CASCADE,
        related_name='coupons'
    )

    discount_percentage = models.PositiveIntegerField(
        default=20
    )

    is_used = models.BooleanField(
        default=False
    )

    valid_till = models.DateTimeField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def is_valid(self):

        return (
            not self.is_used and
            timezone.now() <= self.valid_till
        )

    def __str__(self):
        return self.coupon_code


from django.utils import timezone
from datetime import timedelta


class EmailOTP(models.Model):

    email = models.EmailField()

    otp = models.CharField(
        max_length=6
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    expires_at = models.DateTimeField()

    is_verified = models.BooleanField(
        default=False
    )

    def save(self, *args, **kwargs):

        if not self.expires_at:

            self.expires_at = (
                timezone.now() +
                timedelta(minutes=10)
            )

        super().save(*args, **kwargs)

    def __str__(self):

        return f"{self.email} - {self.otp}"