from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.db import transaction
from django.conf import settings

import razorpay

from apps.store.models import Order, OrderItem
from apps.store.core.cart_manager import Cart

from django.utils import timezone
from apps.customer_engagement.models import CustomerLead, RewardCoupon
from apps.store.services.configuration_service import get_store_config
from apps.store.services.offer_service import get_selected_offer
from apps.store.services.checkout_validation_service import validate_checkout


@require_http_methods(["GET", "POST"])
def checkout(request):

    cart = Cart(request)

    items = cart.get_items()

    if not items:
        return redirect('/cart/')

    if request.method == "GET":

        subtotal = cart.get_total_price()

        config = get_store_config()

        mrp_total = cart.get_total_mrp()

        savings = mrp_total - subtotal

        total_quantity = sum(
            item["quantity"]
            for item in items
        )

        shipping_charge = (
            config.shipping_per_pant
            * total_quantity
        )

        cod_charge = (
            config.cod_charge
            * total_quantity
        )

        reward_coupon = None

        reward_discount = 0

        total_savings = savings 

        final_total = subtotal + shipping_charge + cod_charge

        selected_offer = get_selected_offer(request)

        offer_discount = 0
        offer_title = None
        offer_type = None
        exchange_allowed = True
        offer_percentage = 0

        if selected_offer:

            offer_type = selected_offer.get(
                "type"
            )

            if offer_type == "REWARD":

                offer_percentage = (
                    config.reward_percentage
                )

                exchange_allowed = (
                    not config.reward_requires_exchange_waiver
                )

                offer_title = "EVIBE Reward"

            elif offer_type == "FESTIVAL":

                from apps.store.models import (
                    FestivalOffer
                )

                festival = FestivalOffer.objects.filter(
                    id=selected_offer.get("id")
                ).first()

                if festival:

                    offer_percentage = (
                        festival.discount_percentage
                    )

                    exchange_allowed = (
                        festival.exchange_allowed
                    )

                    offer_title = (
                        festival.title
                    )

            discount_base = (
                subtotal
                + shipping_charge
            )

            offer_discount = round(
                (
                    discount_base
                    * offer_percentage
                ) / 100,
                2
            )

            total_savings = total_savings + offer_discount

            final_total = (
                final_total
                - offer_discount
            )

        # =========================
        # EVIBE AUTO REWARD
        # =========================

        customer_email = request.session.get("evibe_customer_email")

        if customer_email:

            print("SESSION EMAIL:", customer_email)

            lead = CustomerLead.objects.filter(
                email=customer_email
            ).first()

            print("LEAD:", lead)

            if lead:

                coupons = RewardCoupon.objects.filter(
                    customer=lead
                )

                print("ALL COUPONS:", coupons)

                reward_coupon = RewardCoupon.objects.filter(
                    customer=lead,
                    is_used=False,
                    valid_till__gte=timezone.now()
                ).first()

                print("FINAL COUPON:", reward_coupon)

                if reward_coupon:

                    reward_discount = round((
                        subtotal * reward_coupon.discount_percentage  
                    ) / 100, 2)

                    total_savings = total_savings + reward_discount

                    final_total = final_total - reward_discount

                        
        cod_allowed = (
        config.cod_enabled
        and
        final_total <= config.max_cod_order_value
        )

        # =========================
        # PAYMENT SUMMARY
        # =========================

        online_pay_now = final_total

        if cod_allowed:
            cod_pay_now = shipping_charge + cod_charge
            cod_pay_later = subtotal - offer_discount - reward_discount
        else:
            cod_pay_now = 0
            cod_pay_later = 0

        # ==========================================
        # PREPARE DISPLAY DATA FOR CHECKOUT
        # ==========================================

        for item in items:

            unit_mrp = item["product"].price

            line_mrp = unit_mrp * item["quantity"]

            item["unit_mrp"] = unit_mrp
            item["line_mrp"] = line_mrp

        return render(request, "store/checkout.html", {
            "items": items,
            "cart": cart,
            "mrp_total": mrp_total,
            "selected_offer": selected_offer,
            "offer_discount": offer_discount,
            "offer_title": offer_title,
            "exchange_allowed": exchange_allowed,
            "savings": savings,
            "total_savings": total_savings,
            "shipping_charge": shipping_charge,
            "cod_charge": cod_charge,
            "reward_coupon": reward_coupon,
            "reward_discount": reward_discount,
            "final_total": final_total,
            "online_pay_now": online_pay_now,
            "cod_pay_now": cod_pay_now,
            "cod_pay_later": cod_pay_later,
            "cod_allowed": cod_allowed,
        })

    if request.method == "POST":

        validation = validate_checkout(request)
        if not validation.success:
            messages.error(request, validation.message)
            return redirect("/checkout/")

        customer_name = validation.customer_name
        phone = validation.phone
        email = validation.email
        house_no = request.POST.get("house_no", "").strip()
        building = request.POST.get("building", "").strip()
        street = request.POST.get("street", "").strip()
        landmark = request.POST.get("landmark", "").strip()

        address = "\n".join(
            part
            for part in [
                house_no,
                building,
                street,
                landmark,
            ]
            if part
        )
        
        
        city = validation.city
        district = validation.district
        state = validation.state
        pincode = request.POST.get('pincode')
        payment_method = request.POST.get('payment_method')
        

        subtotal = cart.get_total_price()

        config = get_store_config()


        total_quantity = sum(
            item["quantity"]
            for item in items
        )
        
        shipping_charge = (
            config.shipping_per_pant
            * total_quantity
        )

        cod_charge = (
            config.cod_charge
            * total_quantity
        )

        reward_discount = 0

        reward_coupon = None

        selected_offer = get_selected_offer(request)

        offer_type = None
        offer_title = None
        offer_percentage = 0
        offer_discount = 0
        exchange_allowed = True

        if payment_method == "ONLINE":
            cod_charge = 0
            total_amount = (
                subtotal
                + shipping_charge
            )
            advance_paid_amount = total_amount
            amount_collectable = 0
        else:
            total_amount = (
                subtotal
                + shipping_charge
                + cod_charge
            )
            advance_paid_amount = (
                shipping_charge
                + cod_charge
            )
            amount_collectable = subtotal

        if payment_method == "COD":

            if not config.cod_enabled:

                messages.error(
                    request,
                    "Cash on Delivery is currently unavailable."
                )

                return redirect("/checkout/")

            if total_amount > config.max_cod_order_value:

                messages.error(
                    request,
                    "COD is not available for this order value."
                )

                return redirect("/checkout/")
            
            if selected_offer:

                offer_type = selected_offer.get(
                    "type"
                )

                if offer_type == "REWARD":

                    offer_percentage = (
                        config.reward_percentage
                    )

                    exchange_allowed = (
                        not config.reward_requires_exchange_waiver
                    )

                    offer_title = "EVIBE Reward"

                elif offer_type == "FESTIVAL":

                    from apps.store.models import FestivalOffer

                    festival = FestivalOffer.objects.filter(
                        id=selected_offer.get("id")
                    ).first()

                    if festival:

                        offer_percentage = (
                            festival.discount_percentage
                        )

                        exchange_allowed = (
                            festival.exchange_allowed
                        )

                        offer_title = (
                            festival.title
                        )

                discount_base = (
                    subtotal
                    + shipping_charge
                )

                offer_discount = round(
                    (
                        discount_base
                        * offer_percentage
                    ) / 100,
                    2
                )

                total_amount = (
                    total_amount
                    - offer_discount
                )   

        # =========================
        # EVIBE REWARD
        # =========================

        customer_email_session = request.session.get(
            "evibe_customer_email"
        )

        if customer_email_session:

            lead = CustomerLead.objects.filter(
                email=customer_email_session
            ).first()

            if lead:

                reward_coupon = RewardCoupon.objects.filter(
                    customer=lead,
                    is_used=False,
                    valid_till__gte=timezone.now()
                ).first()

                if reward_coupon:

                    reward_discount = round((
                        subtotal * reward_coupon.discount_percentage
                    ) / 100, 2)

                    total_amount = total_amount - reward_discount

        with transaction.atomic():

            order = Order.objects.create(
                customer_name=customer_name,
                phone=phone,
                email=email,
                address=address,
                city=city,
                district=district,
                state=state,
                pincode=pincode,
                payment_method=payment_method,
                status='CREATED',
                subtotal=subtotal,
                shipping_charge=shipping_charge,
                total_amount=total_amount,
                offer_type=offer_type,
                offer_title=offer_title,
                offer_discount_percentage=offer_percentage,
                offer_discount_amount=offer_discount,
                exchange_allowed=exchange_allowed,
                cod_charge=cod_charge,
                advance_paid_amount=advance_paid_amount,
                amount_collectable=amount_collectable,
                reward_discount=reward_discount,
                reward_coupon_code=reward_coupon.coupon_code if reward_coupon else None
            )

            for item in items:

                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    variant=item['variant'],
                    quantity=item['quantity'],
                    price=item['product'].get_final_price()
                )

        # ONLINE -> Pay Full Amount
        # COD -> Pay Only Advance
        if payment_method == "ONLINE":
            razorpay_amount = total_amount
        else:
            razorpay_amount = advance_paid_amount


        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )

        data = {
            "amount": int(razorpay_amount * 100),
            "currency": "INR",
            "payment_capture": 1,
        }

        razorpay_order = client.order.create(data)
        
        order.razorpay_order_id = razorpay_order["id"]

        order.save()

        return render(
            request,
            "store/razorpay_checkout.html",
            {
                "order": order,
                "razorpay_key": settings.RAZORPAY_KEY_ID,
                "razorpay_order_id": razorpay_order["id"],
                "amount": int(razorpay_amount * 100),
                "customer_name": customer_name,
                "phone": phone,
            },
        )

        # =========================
        # MARK REWARD USED
        # =========================

        if reward_coupon:

            reward_coupon.is_used = True

            reward_coupon.save()

        cart.clear()

        from apps.store.services.offer_service import clear_selected_offer

        clear_selected_offer(request)

        return redirect('/order-success/')


def order_success(request):

    return render(request, "store/order_success.html")