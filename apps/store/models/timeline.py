from django.db import models
from .order import Order


class OrderTimeline(models.Model):

    EVENT_TYPES = [
        ('CREATED', 'Order Created'),
        ('STATUS_CHANGED', 'Status Changed'),
        ('PAYMENT', 'Payment'),
        ('SHIPMENT', 'Shipment'),
        ('RETURN', 'Return'),
        ('REFUND', 'Refund'),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="timeline")

    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)

    message = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.order.id} - {self.event_type}"