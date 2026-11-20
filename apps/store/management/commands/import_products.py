import csv
import os
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.store.models import Product, ProductVariant, ProductImage, Category


class Command(BaseCommand):
    help = "Import products, variants and link images"

    def handle(self, *args, **kwargs):

        # ----------------------------
        # 1️⃣ IMPORT PRODUCTS
        # ----------------------------
        with open('products.csv', newline='', encoding='cp1252') as file:
            reader = csv.DictReader(file)

            for row in reader:

                # 🔹 Handle Category (ForeignKey)
                category_name = row.get('category', '').strip().lower()
                category_obj = None

                if category_name:
                    category_obj, _ = Category.objects.get_or_create(
                        name=category_name
                    )

                # 🔹 Create or Update Product safely
                product, created = Product.objects.update_or_create(
                    product_code=row['product_code'],
                    defaults={
                        'name': row['name'],
                        'category': category_obj,
                        'cost_price': Decimal(row['cost_price']),
                        'mrp': Decimal(row['mrp']),
                        'price': Decimal(row['price']),
                        'description': row.get('description', '').strip(),
                        'active': row['active'].strip().lower() == 'true'
                    }
                )

                if created:
                    self.stdout.write(self.style.SUCCESS(
                        f"Created Product: {product.product_code}"
                    ))
                else:
                    self.stdout.write(
                        f"Updated Product: {product.product_code}"
                    )

        # ----------------------------
        # 2️⃣ IMPORT VARIANTS
        # ----------------------------
        with open('variants.csv', newline='', encoding='cp1252') as file:
            reader = csv.DictReader(file)

            for row in reader:
                try:
                    product = Product.objects.get(
                        product_code=row['product_code']
                    )

                    # Prevent duplicate variants
                    ProductVariant.objects.update_or_create(
                        product=product,
                        size=row['size'],
                        defaults={
                            'stock': int(row['stock'])
                        }
                    )

                    self.stdout.write(self.style.SUCCESS(
                        f"Variant {row['size']} synced for {product.product_code}"
                    ))

                except Product.DoesNotExist:
                    self.stdout.write(self.style.ERROR(
                        f"Product not found: {row['product_code']}"
                    ))


        # ----------------------------
        # LINK IMAGES
        # ----------------------------
        products = Product.objects.select_related("category").all()

        for product in products:

            # Category folder
            category_name = (
                product.category.name.strip().lower()
                if product.category
                else "uncategorized"
            )

            # Resolve the actual category folder, preserving its capitalization.
            products_root = os.path.join(settings.MEDIA_ROOT, "products")
            category_folder = category_name

            if os.path.isdir(products_root):
                for folder_name in os.listdir(products_root):
                    if folder_name.lower() == category_name.lower():
                        category_folder = folder_name
                        break

            # media/products/<actual-category-folder>/<product_code>/original/
            original_folder = os.path.join(
                products_root,
                category_folder,
                product.product_code,
                "original"
            )

            if not os.path.exists(original_folder):
                self.stdout.write(
                    self.style.WARNING(
                        f"Image folder not found: {original_folder}"
                    )
                )
                continue

            # Remove old image records
            ProductImage.objects.filter(product=product).delete()

            # Find supported image files
            image_files = sorted(
                f for f in os.listdir(original_folder)
                if f.lower().endswith(
                    (".jpg", ".jpeg", ".png", ".webp")
                )
            )

            # Create ProductImage records
            for filename in image_files:

                image_path = os.path.join(
                    "products",
                    category_folder,
                    product.product_code,
                    "original",
                    filename
                ).replace("\\", "/")

                ProductImage.objects.create(
                    product=product,
                    original_image=image_path
                )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Images synced for {product.product_code}"
                )
            )