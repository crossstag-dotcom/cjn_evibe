from django.contrib import admin
from django.utils.html import format_html

from ..models import Category, Product, ProductVariant, ProductImage


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    ordering = ("name",)


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0


class ProductImageInline(admin.TabularInline):
    model = ProductImage
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


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

    list_display_links = ("product_code",)
    
    list_display = (
        "product_code",
        "name",
        "category",
        "price",
        "offer_price",
        "is_best_seller",
        "best_seller_order",
        "is_featured",
        "featured_order",
        "is_new_arrival",
        "new_arrival_order",
        "all_products_order",
        "active",
    )

    list_editable = (
        "is_featured",
        "featured_order",
        "is_best_seller",
        "best_seller_order",
        "is_new_arrival",
        "new_arrival_order",
        "all_products_order",
    )

    list_filter = (
        "active",
        "is_best_seller",
        "is_featured",
        "is_new_arrival",
    )

    search_fields = ("name", "product_code")

    inlines = [ProductVariantInline, ProductImageInline]

    fieldsets = (
        ("Basic Information", {
            "fields": ("product_code", "name", "category", "slug")
        }),

        ("Pricing", {
            "fields": ("cost_price", "mrp", "price", "offer_price", "offer_end")
        }),

        ("Display Controls", {
            "fields": (
                "is_featured",
                "is_best_seller",
                "is_new_arrival",
                "show_countdown",
                "all_products_order",
                "active",
            )
        }),
    )