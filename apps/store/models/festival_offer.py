from django.db import models


class FestivalOffer(models.Model):

    title = models.CharField(
        max_length=200
    )

    banner_text = models.CharField(
        max_length=500,
        blank=True
    )

    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2
    )

    minimum_pants_required = models.PositiveIntegerField(
        default=1
    )

    exchange_allowed = models.BooleanField(
        default=True
    )

    is_active = models.BooleanField(
        default=True
    )

    start_date = models.DateTimeField()

    end_date = models.DateTimeField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return self.title