from django.db import models
from django.core.validators import (
    MinValueValidator,
    MaxValueValidator
)

from apps.store.services.image_service import generate_optimized_images
from apps.customer_engagement.models import CustomerLead


class ProductReview(models.Model):

    product = models.ForeignKey(
        "store.Product",
        on_delete=models.CASCADE,
        related_name="reviews"
    )

    customer = models.ForeignKey(
        CustomerLead,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviews"
    )

    display_name = models.CharField(
        max_length=100
    )

    city = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    rating = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5)
        ]
    )

    review = models.TextField(
        max_length=2000
    )

    is_verified_buyer = models.BooleanField(
        default=False
    )

    is_featured = models.BooleanField(
        default=False
    )

    is_approved = models.BooleanField(
        default=False
    )

    helpful_count = models.PositiveIntegerField(
        default=0
    )

    admin_notes = models.TextField(
        blank=True,
        null=True
    )

    created_by_customer = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:

        ordering = ["-created_at"]

        constraints = [
            models.UniqueConstraint(
                fields=["product", "customer"],
                condition=models.Q(
                    created_by_customer=True,
                    customer__isnull=False
                ),
                name="unique_customer_review_per_product"
            )
        ]

    def __str__(self):
            return f"{self.product.name} - {self.display_name}"


class ReviewImage(models.Model):

    review = models.ForeignKey(
        ProductReview,
        on_delete=models.CASCADE,
        related_name="images"
    )

    original_image = models.ImageField(
        upload_to="reviews/%Y/%m/%d/original/"
    )

    optimized = models.JSONField(
        blank=True,
        null=True
    )

    show_in_gallery = models.BooleanField(
        default=False
    )

    display_order = models.PositiveIntegerField(
        default=0
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def save(self, *args, **kwargs):

        super().save(*args, **kwargs)

        generate_optimized_images(self)

    class Meta:
        ordering = [
            "display_order",
            "id"
        ]

    def __str__(self):
        return f"Review Image #{self.id}"


class CustomerStylePhoto(models.Model):

    product = models.ForeignKey(
        "store.Product",
        on_delete=models.CASCADE,
        related_name="style_photos"
    )

    original_image = models.ImageField(
        upload_to="customer_style/%Y/%m/%d/original/"
    )

    optimized = models.JSONField(
        blank=True,
        null=True
    )

    display_order = models.PositiveIntegerField(
        default=0
    )

    active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def save(self, *args, **kwargs):

        super().save(*args, **kwargs)

        generate_optimized_images(self)

    class Meta:
        ordering = [
            "display_order",
            "id"
        ]

    def __str__(self):
        return (
            f"{self.product.name} "
            f"Style Photo"
        )