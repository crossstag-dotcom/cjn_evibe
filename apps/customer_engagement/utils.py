import random
import string

from django.core.mail import send_mail

from django.conf import settings

from .models import EmailOTP

from django.utils import timezone
from datetime import timedelta

from .models import RewardCoupon


def generate_coupon_code():

    prefix = "EVIBE"

    random_part = ''.join(
        random.choices(
            string.ascii_uppercase + string.digits,
            k=6
        )
    )

    return f"{prefix}-{random_part}"


def create_signup_coupon(customer):

    coupon = RewardCoupon.objects.create(

        customer=customer,

        coupon_code=generate_coupon_code(),

        discount_percentage=20,

        valid_till=timezone.now() + timedelta(days=7)

    )

    return coupon

def generate_otp():

    return str(
        random.randint(100000, 999999)
    )


def send_email_otp(email):

    EmailOTP.objects.filter(
        email=email
    ).delete()

    otp = generate_otp()

    email_otp = EmailOTP.objects.create(

        email=email,

        otp=otp

    )

    send_mail(
        subject='Your EVIBE Verification OTP',
        message=f'''

Your EVIBE OTP is:

{otp}

This OTP is valid for 10 minutes.

- EVIBE Team
''',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )

    return email_otp