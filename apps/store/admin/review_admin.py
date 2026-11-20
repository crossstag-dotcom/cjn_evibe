from django.contrib import admin
from django.utils.html import format_html

from ..models import (
    ProductReview,
    ReviewImage,
    CustomerStylePhoto
)


class ReviewImageInline(admin.TabularInline):
    model = ReviewImage
    extra = 0

    readonly_fields = ("image_preview",)

    def image_preview(self, obj):

        if obj.original_image:
            return format_html(
                '<img src="{}" width="100" />',
                obj.original_image.url
            )

        return "-"

    image_preview.short_description = "Preview"


@admin.action(description="Approve selected reviews")
def approve_reviews(modeladmin, request, queryset):

    queryset.update(is_approved=True)


@admin.action(description="Reject selected reviews")
def reject_reviews(modeladmin, request, queryset):

    queryset.update(is_approved=False)


@admin.action(description="Feature selected reviews")
def feature_reviews(modeladmin, request, queryset):

    queryset.update(is_featured=True)


@admin.action(description="Remove featured status")
def unfeature_reviews(modeladmin, request, queryset):

    queryset.update(is_featured=False)


@admin.action(description="Mark as verified buyer")
def verify_reviews(modeladmin, request, queryset):

    queryset.update(is_verified_buyer=True)


@admin.action(description="Remove verified buyer badge")
def unverify_reviews(modeladmin, request, queryset):

    queryset.update(is_verified_buyer=False)


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "product",
        "display_name",
        "rating",
        "is_verified_buyer",
        "is_featured",
        "is_approved",
        "created_at",
    )

    list_filter = (
        "rating",
        "is_verified_buyer",
        "is_featured",
        "is_approved",
        "created_at",
    )

    search_fields = (
        "display_name",
        "product__name",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    inlines = [ReviewImageInline]

    actions = [
        approve_reviews,
        reject_reviews,
        feature_reviews,
        unfeature_reviews,
        verify_reviews,
        unverify_reviews,
    ]


@admin.register(CustomerStylePhoto)
class CustomerStylePhotoAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "product",
        "display_order",
        "active",
        "image_preview",
        "created_at",
    )

    list_filter = (
        "active",
        "product",
    )

    search_fields = (
        "product__name",
    )

    readonly_fields = (
        "image_preview",
        "created_at",
    )

    def image_preview(self, obj):

        if obj.original_image:
            return format_html(
                '<img src="{}" width="120" />',
                obj.original_image.url
            )

        return "-"

    image_preview.short_description = "Preview"