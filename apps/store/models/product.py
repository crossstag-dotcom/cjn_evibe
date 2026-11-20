from django.db import models
from django.utils.text import slugify
from django.utils import timezone
from .category import Category
from apps.store.services.image_service import generate_optimized_images


class Product(models.Model):
    product_code = models.CharField(max_length=100, unique=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name="products"
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
    mrp = models.DecimalField(max_digits=10, decimal_places=2)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)

    offer_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    offer_end = models.DateTimeField(null=True, blank=True)
    
    #  Admin control flags
    is_featured = models.BooleanField(default=False)
    featured_order = models.PositiveIntegerField(null=True, blank=True)

    is_best_seller = models.BooleanField(default=False)
    best_seller_order = models.PositiveIntegerField(null=True, blank=True)

    is_new_arrival = models.BooleanField(default=False)
    new_arrival_order = models.PositiveIntegerField(null=True, blank=True)
    all_products_order = models.IntegerField(null=True, blank=True, help_text="Controls order in View All Products page")

    show_countdown = models.BooleanField(default=False)

    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_offer_active(self):
        return (
            self.offer_price and
            self.offer_end and
            self.offer_end > timezone.now()
        )

    def get_final_price(self):
        if self.is_offer_active():
            return self.offer_price
        return self.price
    
    def get_discount_percentage(self):
        final_price = self.get_final_price()

        if self.mrp > 0:
            discount = ((self.mrp - final_price) / self.mrp) * 100
            return round(discount)

        return 0

    def get_discount_amount(self):
        if self.is_offer_active():
            return self.mrp - self.offer_price
        return self.mrp - self.price

    def save(self, *args, **kwargs):
        base_slug = slugify(f"{self.product_code}-{self.name}")
        slug = base_slug
        counter = 1

        while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        self.slug = slug

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    size = models.CharField(max_length=10)
    stock = models.IntegerField()

    def __str__(self):
        return f"{self.product.name} - {self.size}"
    

# ProductImage model handles:
# 1. Storing the original uploaded product image.
# 2. Automatically generating optimized WebP images (400px, 800px, 1200px).
# 3. Saving optimized image paths inside a JSONField for fast template access.
# 
# Why this approach?
# - Keeps original image untouched.
# - Improves performance using optimized images.
# - Avoids template path manipulation.
# - Centralizes image processing logic inside the model (production-safe).
class ProductImage(models.Model):    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images"
    )

    original_image = models.ImageField(
        upload_to="products/%Y/%m/%d/original/",
        null=True,
        blank=True
    )

    optimized = models.JSONField(blank=True, null=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        generate_optimized_images(self)

    def __str__(self):
        return f"{self.product.name}"
