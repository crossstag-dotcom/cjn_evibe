import json
import re

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .utils import send_email_otp
from .models import CustomerLead
from .utils import create_signup_coupon

from django.utils import timezone

from .models import EmailOTP
from django.shortcuts import redirect


EMAIL_REGEX = r'^[\w\.-]+@[\w\.-]+\.\w+$'

@csrf_exempt
def send_otp(request):

    if request.method != "POST":

        return JsonResponse({

            "success": False,
            "message": "Invalid request method"

        })

    try:

        data = json.loads(request.body)

        email = data.get("email", "").strip().lower()

        # EMAIL VALIDATION
        if not re.match(EMAIL_REGEX, email):

            return JsonResponse({

                "success": False,
                "message": "Please enter a valid email."

            })


        existing_otp = EmailOTP.objects.filter(
            email=email,
            is_verified=False
        ).order_by('-created_at').first()

        if existing_otp:

            seconds = (
                timezone.now() -
                existing_otp.created_at
            ).seconds

            if seconds < 30:

                return JsonResponse({

                    "success": False,

                    "message":
                    "Please wait 30 seconds before requesting another OTP."

                })
        # SEND OTP
        send_email_otp(email)

        return JsonResponse({

            "success": True,
            "message": "OTP sent successfully."

        })

    except Exception as e:

        return JsonResponse({

            "success": False,
            "message": str(e)

        })

@csrf_exempt
def verify_otp(request):

    if request.method != "POST":

        return JsonResponse({

            "success": False,
            "message": "Invalid request method"

        })

    try:

        data = json.loads(request.body)

        email = data.get("email", "").strip().lower()

        otp = data.get("otp", "").strip()

        preferred_style = data.get(
            "preferred_style",
            ""
        )

        # CHECK OTP EXISTS
        email_otp = EmailOTP.objects.filter(

            email=email,

            otp=otp,

            is_verified=False

        ).first()

        if not email_otp:

            return JsonResponse({

                "success": False,
                "message": "Invalid OTP."

            })

        # CHECK OTP EXPIRY
        if timezone.now() > email_otp.expires_at:

            return JsonResponse({

                "success": False,
                "message": "OTP expired."

            })

        # MARK VERIFIED
        email_otp.is_verified = True

        email_otp.save()

        # CHECK EXISTING CUSTOMER
        customer = CustomerLead.objects.filter(
            email=email
        ).first()

        is_new_user = False

        if not customer:
            is_new_user = True

        from .models import RewardCoupon

        active_coupon = RewardCoupon.objects.filter(
            customer=customer,
            is_used=False
        ).first()

        new_user = False

        # NEW CUSTOMER
        if not customer:

            customer = CustomerLead.objects.create(

                name=email.split("@")[0],

                email=email,

                login_provider="email_otp",

                preferred_style=preferred_style,

                session_id=request.session.session_key

            )

            new_user = True

        # CREATE COUPON ONLY FOR NEW USER
        coupon = None

        if new_user:

            coupon = create_signup_coupon(
                customer
            )

        # CREATE SESSION LOGIN
        request.session[
            'evibe_customer_id'
        ] = customer.id

        request.session[
            'evibe_customer_name'
        ] = customer.name

        request.session[
            'evibe_customer_email' 
        ] = customer.email


        response_data = {

            "success": True,

            "customer_name": customer.name,

            "new_user": new_user,

            "is_new_user": new_user,

            "message": "OTP verified successfully"

        }

        # ONLY SEND COUPON FOR NEW USERS
        if coupon:

            response_data["coupon_code"] = (
                coupon.coupon_code
            )

            response_data["valid_till"] = (
                coupon.valid_till.strftime(
                    "%d %b %Y"
                )
            )
        elif active_coupon:

            response_data["coupon_code"] = (
                active_coupon.coupon_code
            )

            response_data["valid_till"] = (
                active_coupon.valid_till.strftime(
                    "%d %b %Y"
                )
            )

        return JsonResponse(response_data)

    except Exception as e:

        return JsonResponse({

            "success": False,
            "message": str(e)

        })


@csrf_exempt
def signup_lead(request):

    if request.method != "POST":

        return JsonResponse({
            "success": False,
            "message": "Invalid request method"
        })

    try:
        name = request.POST.get("name")
        email = request.POST.get("email")
        login_provider = "signup_popup"
        preferred_style = request.POST.get("preferred_style","")

        # EMAIL VALIDATION
        if not re.match(EMAIL_REGEX, email):

            return JsonResponse({

                "success": False,
                "message": "Please enter a valid email address."

            })

        # DUPLICATE EMAIL CHECK
        if CustomerLead.objects.filter(email=email).exists():

            return JsonResponse({

                "success": False,
                "message": "This email already unlocked a reward."

            })

        # CREATE CUSTOMER
        customer = CustomerLead.objects.create(

            name=name,

            email=email,

            login_provider=login_provider,

            preferred_style=preferred_style,

            session_id=request.session.session_key

        )

        # CREATE COUPON
        coupon = create_signup_coupon(customer)

        # LOGIN CUSTOMER
        request.session['evibe_customer_id'] = customer.id

        request.session['evibe_customer_name'] = customer.name

        request.session['evibe_customer_email'] = customer.email

        return JsonResponse({

            "success": True,

            "coupon_code": coupon.coupon_code,

            "discount_percentage": coupon.discount_percentage,

            "valid_till": coupon.valid_till.strftime("%d %b %Y"),

            "message": "Reward unlocked successfully"

        })

    except Exception as e:

        return JsonResponse({

            "success": False,
            "message": str(e)

        })
    
def logout_view(request):

    request.session.flush()

    return redirect('/')