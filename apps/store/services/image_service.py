from PIL import Image
import os
from django.conf import settings

SIZES = [400, 800, 1200]

def generate_optimized_images(instance):

    if instance.optimized and os.path.exists(instance.original_image.path):
         return

    original_path = instance.original_image.path

    # Example:
    # media/products/Evibe_11223_Denim_Blue/original/image.jpg

    product_folder = os.path.dirname(os.path.dirname(original_path))
    optimized_folder = os.path.join(product_folder, "optimized")

    os.makedirs(optimized_folder, exist_ok=True)

    filename = os.path.splitext(
        os.path.basename(original_path)
    )[0]

    optimized_data = {}

    for size in SIZES:

        output_filename = f"{filename}_{size}.webp"
        output_path = os.path.join(optimized_folder, output_filename)

        if not os.path.exists(output_path):
            img = Image.open(original_path)
            img.thumbnail((size, size))
            img.save(output_path, "WEBP", quality=85)

        relative_path = output_path.replace(settings.MEDIA_ROOT, "").replace("\\", "/")

        optimized_data[str(size)] = f"{settings.MEDIA_URL}{relative_path}"

    instance.optimized = optimized_data
    instance.save(update_fields=["optimized"])
