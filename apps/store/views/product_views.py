from django.db.models import F, Avg
from django.shortcuts import render, get_object_or_404
from apps.store.models import Product, Category, ProductVariant, ProductReview, CustomerStylePhoto
from apps.analytics.models import ProductView
from django.http import HttpRequest

from pathlib import Path
import geoip2.database


# Helper function to fetch testimonials for the homepage or product pages.
def get_testimonials():

    return ProductReview.objects.filter(
        is_approved=True,
        rating__gte=4,
        images__isnull=False
    ).prefetch_related(
        "images",
        "customer"
    ).distinct().order_by(
        "-created_at"
    )[:20]

# Views for product listing, product details, and category-wise product listing.
def product_list(request):

    products = Product.objects.filter(active=True).order_by(
        F('all_products_order').asc(nulls_last=True)
    )[:6]

    featured_products = Product.objects.filter(
        is_featured=True,
        active=True,
        featured_order__isnull=False
    ).order_by('featured_order')[:6]

    best_sellers = Product.objects.filter(
        is_best_seller=True,
        active=True,
        best_seller_order__isnull=False
    ).order_by('best_seller_order')[:6]

    new_arrivals = Product.objects.filter(
    active=True,
    is_new_arrival=True
    ).order_by('new_arrival_order')[:6]

    return render(request, "store/product_list.html", {
        "products": products,
        "featured_products": featured_products,
        "best_sellers": best_sellers,
        "new_arrivals": new_arrivals,
        "testimonials": get_testimonials(),
    })

# For product detail view, we will also track product views and user city for analytics purposes.
def get_user_city(request):
    """
    Get the visitor's city using their IP address
    and the local MaxMind GeoLite2 City database.
    """

    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

    if forwarded_for:
        ip = forwarded_for.split(",")[0].strip()
    else:
        ip = request.META.get("REMOTE_ADDR")

    # Local development fallback
    if ip in ["127.0.0.1", "localhost", "::1", None]:
        return "Bangalore"

    geoip_db = (
        Path(__file__).resolve().parents[3]
        / "data"
        / "geoip"
        / "GeoLite2-City.mmdb"
    )

    try:
        with geoip2.database.Reader(str(geoip_db)) as reader:
            response = reader.city(ip)

            city = response.city.name

            if city:
                return city

    except Exception as e:
        print(f"GeoIP lookup failed for {ip}: {e}")

    return "Unknown"


# Category-wise product listing with optional size filtering.
def category_products(request, slug):

    category = get_object_or_404(Category, name__iexact=slug)

    products = Product.objects.filter(
        category=category,
        active=True
    ).prefetch_related('images')

    size = request.GET.get('size')

    if size:
        products = products.filter(variants__size=size)

    products = products.order_by(
        F('all_products_order').asc(nulls_last=True),
        '-created_at'
    ).distinct()

    available_sizes = ProductVariant.objects.filter(
    product__category=category,
    product__active=True
    ).values_list(
        'size',
        flat=True
    ).distinct().order_by('size')

    return render(request, "store/category.html", {
        "category": category,
        "products": products,
        "available_sizes": available_sizes,
        "selected_size": size,
        "clear_filter_url": "category_products",
        "testimonials": get_testimonials(),  
    })

# Views for product listing, product details, and category-wise product listing.
from django.db.models import F

def all_products(request):

    products = Product.objects.filter(
        active=True
    ).prefetch_related('images')

    size = request.GET.get('size')

    if size:
        products = products.filter(
            variants__size=size
        )

    products = products.order_by(
        F('all_products_order').asc(nulls_last=True)
    ).distinct()

    available_sizes = ProductVariant.objects.filter(
        product__active=True
    ).values_list(
        'size',
        flat=True
    ).distinct().order_by('size')


    return render(request, 'store/all_products.html', {
        'products': products,
        'available_sizes': available_sizes,
        'selected_size': size,
        'testimonials': get_testimonials(),
    })


# For product detail view, we will also track product views and user city for analytics purposes.


def product_detail(request, slug):

    product = get_object_or_404(
        Product,
        slug=slug
    )

    # ===============================
    # REVIEWS
    # ===============================

    gallery_photos = CustomerStylePhoto.objects.filter(
        product=product,
        active=True
    ).order_by(
        "display_order"
    )

    featured_reviews = ProductReview.objects.filter(
        product=product,
        is_approved=True,
        is_featured=True
    ).prefetch_related(
        "images"
    )[:4]

    review_queryset = ProductReview.objects.filter(
        product=product,
        is_approved=True
    )

    review_count = review_queryset.count()

    average_rating = (
        review_queryset.aggregate(
            Avg("rating")
        )["rating__avg"]
        or 0
    )


    # ===============================
    # PRODUCT VIEW TRACKING
    # ===============================

    session_id = request.session.session_key

    if not session_id:

        request.session.create()

        session_id = (
            request.session.session_key
        )

    city = get_user_city(request)

    already_viewed = ProductView.objects.filter(
        product=product,
        session_id=session_id
    ).exists()

    if not already_viewed:

        ProductView.objects.create(
            product=product,
            session_id=session_id,
            city=city
        )

    # ===============================
    # SIMILAR PRODUCTS
    # ===============================

    similar_products = (
        Product.objects.filter(
            active=True,
            category=product.category
        )
        .exclude(id=product.id)
        .prefetch_related("images")
        .order_by("-created_at")[:4]
    )

    out_of_stock_variants = product.variants.filter(
        stock__lte=0
    ).order_by("size")

    out_of_stock_sizes = list(
        out_of_stock_variants.values_list(
            "size",
            flat=True
        )
    )

    has_out_of_stock = out_of_stock_variants.exists()

    return render(
        request,
        "store/product_detail.html",
        {
            "product": product,

            # Reviews
            "gallery_photos": gallery_photos,
            "featured_reviews": featured_reviews,
            "review_count": review_count,
            "average_rating": round(
                average_rating,
                1
            ),
            "similar_products": similar_products,
            "out_of_stock_sizes": out_of_stock_sizes,
            "has_out_of_stock": has_out_of_stock,
        }
    )

def new_arrivals(request):

    size = request.GET.get("size")

    products = Product.objects.filter(
        active=True,
        is_new_arrival=True
    ).prefetch_related("images").order_by(
        F("new_arrival_order").asc(nulls_last=True),
        "-created_at"
    )

    if size:
        products = products.filter(
            variants__size=size
        )

    available_sizes = ProductVariant.objects.filter(
        product__is_new_arrival=True,
        product__active=True
    ).values_list(
        "size",
        flat=True
    ).distinct().order_by("size")

    return render(request, "store/category.html", {
        "products": products,
        "available_sizes": available_sizes,
        "selected_size": size,
        "clear_filter_url": "new_arrivals",
        "category": {
            "name": "New Arrivals"
        },
        "testimonials": get_testimonials(),
    })


def best_sellers(request):

    size = request.GET.get("size")

    products = Product.objects.filter(
        active=True,
        is_best_seller=True
    ).prefetch_related("images").order_by(
        F("best_seller_order").asc(nulls_last=True),
        "-created_at"
    )

    if size:
        products = products.filter(
            variants__size=size
        )

    available_sizes = ProductVariant.objects.filter(
        product__is_best_seller=True,
        product__active=True
    ).values_list(
        "size",
        flat=True
    ).distinct().order_by("size")

    return render(request, "store/category.html", {
        "products": products,
        "available_sizes": available_sizes,
        "selected_size": size,
        "clear_filter_url": "best_sellers",
        "category": {
            "name": "Best Sellers"
        },
        "testimonials": get_testimonials(),
    })

def denim_coming_soon(request):

    return render(
        request,
        "store/coming_soon.html",
        {
            "title": "EVIBE Denim",
            "subtitle": "Launching Soon",
        },
    )