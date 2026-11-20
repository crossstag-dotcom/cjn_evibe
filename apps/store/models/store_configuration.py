from django.db import models


class StoreConfiguration(models.Model):

    # -----------------------
    # SHIPPING
    # -----------------------

    shipping_per_pant = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=149
    )

    # -----------------------
    # COD
    # -----------------------

    cod_charge = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=50
    )

    cod_enabled = models.BooleanField(
        default=True
    )

    max_cod_order_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=5000
    )

    cod_advance_required = models.BooleanField(
        default=True
    )

    # -----------------------
    # REWARDS
    # -----------------------

    reward_system_enabled = models.BooleanField(
        default=True
    )

    reward_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=5
    )

    minimum_pants_for_reward = models.PositiveIntegerField(
        default=4
    )

    reward_requires_exchange_waiver = models.BooleanField(
        default=True
    )

    # -----------------------
    # RETURNS
    # -----------------------

    return_window_days = models.PositiveIntegerField(
        default=7
    )

    # -----------------------
    # AUDIT
    # -----------------------

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):

        return "EVIBE Store Configuration"