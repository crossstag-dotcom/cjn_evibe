from django.utils import timezone

from apps.store.models import FestivalOffer
from apps.store.services.configuration_service import (
    get_store_config
)


def get_eligible_offers(total_quantity):

    offers = []

    config = get_store_config()

    # -----------------------
    # Reward Offer
    # -----------------------

    if (
        config.reward_system_enabled
        and
        total_quantity >= config.minimum_pants_for_reward
    ):

        offers.append({
            "type": "REWARD",
            "title": "EVIBE Reward",
            "discount_percentage": float(
                config.reward_percentage
            ),
            "exchange_allowed": (
                not config.reward_requires_exchange_waiver
            ),
        })

    # -----------------------
    # Festival Offer
    # -----------------------

    now = timezone.now()

    festival_offer = (
        FestivalOffer.objects
        .filter(
            is_active=True,
            start_date__lte=now,
            end_date__gte=now
        )
        .order_by("-created_at")
        .first()
    )

    if (
        festival_offer
        and
        total_quantity >= festival_offer.minimum_pants_required
    ):

        offers.append({
            "type": "FESTIVAL",
            "id": festival_offer.id,
            "title": festival_offer.title,
            "discount_percentage": float(
                festival_offer.discount_percentage
            ),
            "exchange_allowed": (
                festival_offer.exchange_allowed
            ),
        })

    return offers

# -----------------------
# Session Management
# -----------------------
def set_selected_offer(request, offer_data):

    request.session["selected_offer"] = offer_data
    request.session.modified = True


def get_selected_offer(request):

    return request.session.get(
        "selected_offer"
    )


def clear_selected_offer(request):

    request.session.pop(
        "selected_offer",
        None
    )

    request.session.modified = True