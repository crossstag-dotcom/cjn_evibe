import re

from dataclasses import dataclass

from django.core.exceptions import ValidationError
from django.core.validators import validate_email

from apps.store.services.pincode_service import (
    get_location_from_pincode,
)


@dataclass
class CheckoutValidationResult:
    success: bool
    message: str = ""

    customer_name: str = ""
    phone: str = ""
    email: str = ""

    city: str = ""
    district: str = ""
    state: str = ""

def validate_checkout(request):

    # --------------------------
    # Customer Name
    # --------------------------

    customer_name = request.POST.get(
        "customer_name",
        ""
    ).strip()

    if not re.fullmatch(r"[A-Za-z ]{2,50}", customer_name):

        return CheckoutValidationResult(
            success=False,
            message="Enter a valid customer name."
        )

    # --------------------------
    # Phone
    # --------------------------

    phone = request.POST.get(
        "phone",
        ""
    ).strip()

    if not re.fullmatch(r"[6-9]\d{9}", phone):

        return CheckoutValidationResult(
            success=False,
            message="Enter a valid mobile number."
        )

    # --------------------------
    # Email
    # --------------------------

    email = request.POST.get(
        "email",
        ""
    ).strip()

    try:
        validate_email(email)

    except ValidationError:

        return CheckoutValidationResult(
            success=False,
            message="Enter a valid email address."
        )

    # --------------------------
    # PIN Code
    # --------------------------

    pincode = request.POST.get(
        "pincode",
        ""
    ).strip()

    location = get_location_from_pincode(
        pincode
    )

    if not location.success:

        return CheckoutValidationResult(
            success=False,
            message=location.message
        )

    # --------------------------
    # Success
    # --------------------------

    return CheckoutValidationResult(
        success=True,
        customer_name=customer_name,
        phone=phone,
        email=email,
        city=location.city,
        district=location.district,
        state=location.state,
    )