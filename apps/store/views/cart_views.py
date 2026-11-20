from django.shortcuts import render, redirect
from django.contrib import messages
from apps.store.core.cart_manager import Cart
from apps.store.models import ProductVariant
from apps.store.services.offer_service import get_eligible_offers, get_selected_offer, set_selected_offer, clear_selected_offer
from apps.store.services.configuration_service import get_store_config

# Cart views for adding, removing, and updating items in the cart, as well as displaying the cart details.
def add_to_cart(request):

    if request.method == "POST":

        variant_id = request.POST.get("variant_id")
        variant = ProductVariant.objects.filter(id=variant_id).first()

        if not variant:
            messages.error(request, "Invalid product variant.")
            return redirect('/')

        if variant.stock <= 0:
            messages.error(request, "Product out of stock.")
            return redirect('/')

        cart = Cart(request)
        cart.add(variant_id)

        # BUY NOW
        if request.POST.get("buy_now") == "1":
            return redirect("/cart/")

        messages.success(request, "Added to cart")
    return redirect(request.META.get('HTTP_REFERER'))


def remove_from_cart(request, variant_id):

    cart = Cart(request)
    cart.remove(variant_id)

    return redirect('cart')


def increase_quantity(request, variant_id):

    cart = Cart(request)
    cart.increase(variant_id)

    return redirect('cart')


def decrease_quantity(request, variant_id):

    cart = Cart(request)
    cart.decrease(variant_id)

    return redirect('cart')


def apply_offer(request):

    offer_type = request.GET.get(
        "type"
    )

    offer_id = request.GET.get(
        "id"
    )

    set_selected_offer(request, {
        "type": offer_type,
        "id": offer_id
    })

    return redirect("cart")

def remove_offer(request):

    clear_selected_offer(request)

    return redirect("cart")

def cart_detail(request):

    cart = Cart(request)

    items = cart.get_items()

    mrp_total = 0
    subtotal = 0

    for item in items:

        mrp_total += item['product'].mrp * item['quantity']
        subtotal += item['product'].get_final_price() * item['quantity']

    total_quantity = sum(
    item["quantity"]
    for item in items
    )

    eligible_offers = get_eligible_offers(
        total_quantity
    )

    selected_offer = get_selected_offer(
        request
    )

    if selected_offer:

        offer_still_valid = False

        for offer in eligible_offers:

            if (
                offer["type"]
                ==
                selected_offer["type"]
            ):
                offer_still_valid = True
                break

        if not offer_still_valid:

            clear_selected_offer(request)

            selected_offer = None  

    savings = mrp_total - subtotal

    config = get_store_config()

    shipping_charge = (
        config.shipping_per_pant
        * total_quantity
    )

    discount_base = float(
        subtotal
        + shipping_charge
    )

    offer_discount = 0
    offer_title = None

    if selected_offer:

        for offer in eligible_offers:

            if offer["type"] == selected_offer["type"]:

                offer_title = offer["title"]

                offer_discount = round(
                    discount_base
                    * offer["discount_percentage"]
                    / 100,
                    2
                )

                break

    estimated_total = round(
        discount_base
        - offer_discount,
        2
    )

    return render(request, 'store/cart.html', {
        'items': items,
        'cart': cart,
        'mrp_total': mrp_total,
        'subtotal': subtotal,
        'eligible_offers': eligible_offers,
        'selected_offer': selected_offer,
        'shipping_charge': shipping_charge,
        'offer_discount': offer_discount,
        'offer_title': offer_title,
        'estimated_total': estimated_total,
        'savings': savings
    })