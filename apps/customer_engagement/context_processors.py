from .models import RewardCoupon
from django.utils import timezone

# Context processor to add customer details to the context
def evibe_customer(request):

    return {

        "evibe_customer_name":
            request.session.get(
                "evibe_customer_name"
            ),

        "reward_coupon":
            request.session.get(
                "reward_coupon"
            )

    }


# Context processor to add reward coupon details to the context

def reward_context(request):

    customer_id = request.session.get(
        "evibe_customer_id"
    )

    if not customer_id:
        return {}

    coupon = RewardCoupon.objects.filter(
        customer_id=customer_id,
        is_used=False,
        valid_till__gt=timezone.now()
    ).first()

    return {

        "reward_coupon":
            coupon.coupon_code if coupon else None,

        "reward_valid_till":
            coupon.valid_till if coupon else None

    }