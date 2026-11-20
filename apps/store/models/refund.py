from django.db import models
from django.conf import settings
from .order import Order

# Refund   
class Refund(models.Model):

    STATUS_CHOICES = [
        ('INITIATED', 'Initiated'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, db_index=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    razorpay_refund_id = models.CharField(max_length=100, blank=True, null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    created_at = models.DateTimeField(auto_now_add=True)

    refunded_at = models.DateTimeField(blank=True, null=True)

    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"Refund #{self.id} - Order {self.order.id}"