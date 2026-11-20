import csv
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.store.models import Pincode
from django.contrib import admin



@admin.register(Pincode)
class PincodeAdmin(admin.ModelAdmin):

    list_display = (
        "pincode",
        "office_name",
        "district",
        "state",
    )

    search_fields = (
        "pincode",
        "office_name",
        "district",
        "state",
    )

    list_filter = (
        "state",
        "district",
    )

    ordering = ("pincode",)

class Command(BaseCommand):
    help = "Import India PIN codes"

    def handle(self, *args, **options):

        csv_file = Path(settings.BASE_DIR) / "data" / "pincodes.csv"

        if not csv_file.exists():
            self.stdout.write(
                self.style.ERROR(f"CSV not found: {csv_file}")
            )
            return

