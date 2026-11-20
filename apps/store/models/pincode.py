from django.db import models


class Pincode(models.Model):
    pincode = models.CharField(
        max_length=6,
        db_index=True
    )

    office_name = models.CharField(max_length=150)

    district = models.CharField(max_length=100)

    state = models.CharField(max_length=100)

    class Meta:
        ordering = ["pincode", "office_name"]
        verbose_name = "Pincode"
        verbose_name_plural = "Pincodes"

        constraints = [
            models.UniqueConstraint(
                fields=["pincode", "office_name"],
                name="unique_pincode_office",
            )
        ]

    def __str__(self):
        return f"{self.pincode} - {self.office_name}"