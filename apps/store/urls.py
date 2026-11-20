from django.urls import path

from django.shortcuts import render

# PRODUCT
from .views.product_views import (
    product_list,
    product_detail,
    category_products,
    all_products
)

from .views.review_views import (
    product_reviews,
    load_more_reviews
)

# CART
from .views.cart_views import (
    cart_detail,
    add_to_cart,
    remove_from_cart,
    increase_quantity,
    decrease_quantity,
    apply_offer,
    remove_offer,
)

# CHECKOUT
from .views.checkout_views import (
    checkout,
    order_success
)

# ORDERS
from .views.order_views import (
    my_orders,
    track_order,
    order_access,
    request_return
)

# WEBHOOKS
from .views.webhook_views import (
    payment_success,
    razorpay_webhook,
    courier_webhook,
    
)

# AJAX
from .views.ajax_views import (
    get_order_items,
    get_pincode_details,
)

from .views.product_views import (
    product_list,
    product_detail,
    category_products,
    all_products
)

from .views.product_views import (
    product_list,
    product_detail,
    category_products,
    all_products,
    new_arrivals,
    best_sellers,
    denim_coming_soon

)


urlpatterns = [

    # PRODUCT
    path("", product_list, name="product_list"),
    path("product/<slug:slug>/", product_detail, name="product_detail"),
    path("product/<slug:slug>/reviews/", product_reviews, name="product_reviews"),
    path("product/<slug:slug>/reviews/load-more/", load_more_reviews, name="load_more_reviews"),
    path("category/<slug:slug>/", category_products, name="category_products"),
    path("new-arrivals/", new_arrivals, name="new_arrivals"),
    path("best-sellers/", best_sellers, name="best_sellers"),
    path('products/all/', all_products, name='all_products'),
    path('denim/',denim_coming_soon, name="denim_coming_soon"),
    # CART
    path("cart/", cart_detail, name="cart"),
    path("cart/add/", add_to_cart, name="add_to_cart"),
    path("cart/remove/<int:variant_id>/", remove_from_cart, name="remove_from_cart"),
    path("cart/increase/<int:variant_id>/", increase_quantity, name="increase_quantity"),
    path("cart/decrease/<int:variant_id>/", decrease_quantity, name="decrease_quantity"),
    path("cart/apply-offer/", apply_offer, name="apply_offer"),
    path("cart/remove-offer/", remove_offer, name="remove_offer"),

    # CHECKOUT
    path("checkout/", checkout, name="checkout"),
    path("order-success/", order_success, name="order_success"),

    # ORDERS
    path("track-order/<int:order_id>/", track_order, name="track_order"),
    path("my-orders/", my_orders, name="my_orders"),
    path("order-access/", order_access, name="order_access"),
    path("request-return/<int:order_id>/", request_return, name="request_return"),
    
    # WEBHOOKS
    path('payment-success/', payment_success, name='payment_success'),
    path("webhook/razorpay/", razorpay_webhook, name="razorpay_webhook"),
    path("courier/webhook/", courier_webhook, name="courier_webhook"),

    # POLICIES
    path(
        "privacy-policy/",
        lambda request: render(request, "store/privacy_policy.html"),
        name="privacy_policy"
    ),

    path(
        "return-policy/",
        lambda request: render(request, "store/return_policy.html"),
        name="return_policy"
    ),

    path(
        "shipping-policy/",
        lambda request: render(request, "store/shipping_policy.html"),
        name="shipping_policy"
    ),

    path(
        "terms-and-conditions/",
        lambda request: render(request, "store/terms.html"),
        name="terms"
    ),

    path(
        "about-us/",
        lambda request: render(request, "store/about_us.html"),
        name="about_us"
    ),
    # AJAX
    path("ajax/order-items/", get_order_items, name="get_order_items"),
    path("ajax/pincode/", get_pincode_details, name="get_pincode_details"),

]   