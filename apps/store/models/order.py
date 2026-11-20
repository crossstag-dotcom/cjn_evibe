from django.db import models
from django.conf import settings
from .product import Product, ProductVariant

# -----------------------
# ORDER AND ORDER ITEM MODELS
# -----------------------
class Order(models.Model):
    STATUS_CHOICES = [
        ('CREATED', 'Created'),
        ('PAID', 'Paid'),
        ('PROCESSING', 'Processing'),
        ('PACKED', 'Packed'),
        ('READY_TO_SHIP', 'Ready to Ship'),
        ('SHIPPED', 'Shipped'),
        ('OUT_FOR_DELIVERY', 'Out For Delivery'),
        ('DELIVERED', 'Delivered'),
        ('RTO', 'Returned To Origin'),
        ('CANCELLED', 'Cancelled'),
    ]

    PAYMENT_CHOICES = [
        ('COD', 'Cash on Delivery'),
        ('ONLINE', 'Online Payment'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PARTIALLY_PAID', 'Partially Paid'),
        ('PAID', 'Paid'),
        ('REFUNDED', 'Refunded'),
    ]

    RETURN_STATUS = [
    ("NONE", "None"),
    ("IN_PROGRESS", "Return In Progress"),
    ("PARTIAL_RETURNED", "Partially Returned"),
    ("FULLY_RETURNED", "Fully Returned"),
    ]

    return_status = models.CharField(
        max_length=20,
        choices=RETURN_STATUS,
        default="NONE"
    )


    customer_name = models.CharField(max_length=200)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20)
    address = models.TextField()
    city = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)

    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='PENDING')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='CREATED', db_index=True)

    #  PRICE FIELDS (MOVE HERE)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cod_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    advance_paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount_collectable = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Offer fields
    offer_type = models.CharField(max_length=30, blank=True,null=True)
    offer_title = models.CharField(max_length=200, blank=True, null=True)
    offer_discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    offer_discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    exchange_allowed = models.BooleanField(default=True)

    # Discount fields
    reward_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    reward_coupon_code = models.CharField(max_length=100, blank=True, null=True)

    # RAZORPAY FIELDS
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=200, blank=True, null=True)
    refund_processed = models.BooleanField(default=False)
    paid_at = models.DateTimeField(blank=True, null=True)

    # Shipping details
    provider_name = models.CharField(max_length=100, blank=True, null=True)
    courier_name = models.CharField(max_length=100, blank=True, null=True)
    awb_code = models.CharField(max_length=100, blank=True, null=True)
    tracking_url = models.URLField(blank=True, null=True)
    
    shipment_id = models.CharField(max_length=100, blank=True, null=True)

    shipped_at = models.DateTimeField(blank=True, null=True)

    shipment_status = models.CharField(max_length=50, blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)


    # RTO details
    rto_reason = models.CharField(max_length=200, blank=True, null=True)

    rto_date = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    stock_restored = models.BooleanField(default=False)

    last_updated_at = models.DateTimeField(auto_now=True)

    stock_deducted = models.BooleanField(default=False)

    def __str__(self):
        return f"Order #{self.id} - {self.customer_name}"
    
# The OrderItem model represents individual items within an order, linking to the main Order and the specific ProductVariant. It tracks the quantity ordered, price, and any returns or refunds associated with that item. The save method includes validation to prevent invalid return or refund quantities, ensuring data integrity. The refundable_quantity method calculates how many units of the item are still eligible for refund based on returns and previous refunds.
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    returned_quantity = models.IntegerField(default=0)
    refunded_quantity = models.IntegerField(default=0)

    def save(self, *args, **kwargs):

        # Prevent warehouse staff entering invalid returned quantity
        if self.returned_quantity > self.quantity:
            raise ValueError("Returned quantity cannot exceed ordered quantity")

        # Prevent refund exceeding returned quantity
        if self.refunded_quantity > self.returned_quantity:
            raise ValueError("Refunded quantity cannot exceed returned quantity")

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} - {self.variant.size} x {self.quantity}"
    
    def refundable_quantity(self):
        return self.returned_quantity - self.refunded_quantity