from django.contrib import admin
from apps.store.models import FestivalOffer


@admin.register(FestivalOffer)
class FestivalOfferAdmin(admin.ModelAdmin):

    list_display = (
        "title",
        "discount_percentage",
        "minimum_pants_required",
        "is_active",
        "start_date",
        "end_date",
    )