import csv
import time
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.store.models import Pincode


class Command(BaseCommand):
    help = "Import India PIN codes from CSV"

    def handle(self, *args, **kwargs):

        csv_file = Path(settings.BASE_DIR) / "data" / "pincodes.csv"

        if not csv_file.exists():
            self.stdout.write(
                self.style.ERROR(f"CSV file not found: {csv_file}")
            )
            return

        self.stdout.write(self.style.SUCCESS("Reading CSV..."))

        batch = []
        batch_size = 1000

        imported = 0
        start_time = time.time()

        with open(csv_file, "r", encoding="utf-8") as file:

            reader = csv.DictReader(file)

            for row in reader:

                batch.append(
                    Pincode(
                        pincode=row["pincode"].strip(),
                        office_name=row["officename"].strip(),
                        district=row["district"].strip(),
                        state=row["statename"].strip(),
                    )
                )

                if len(batch) >= batch_size:

                    Pincode.objects.bulk_create(
                        batch,
                        batch_size=batch_size,
                        ignore_conflicts=True,
                    )

                    imported += len(batch)

                    self.stdout.write(
                        f"Imported {imported:,} records..."
                    )

                    batch.clear()

            if batch:

                Pincode.objects.bulk_create(
                    batch,
                    batch_size=batch_size,
                    ignore_conflicts=True,
                )

                imported += len(batch)

        elapsed = time.time() - start_time

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write(self.style.SUCCESS("PINCODE IMPORT COMPLETED"))
        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write(f"Records Imported : {imported:,}")
        self.stdout.write(f"Time Taken       : {elapsed:.2f} seconds")
        self.stdout.write(self.style.SUCCESS("=" * 50))