from django.shortcuts import (
    render,
    get_object_or_404
)

from django.http import JsonResponse

from django.core.paginator import (
    Paginator
)

from django.db.models import Avg

from apps.store.models import (
    Product,
    ProductReview
)


def product_reviews(request, slug):

    product = get_object_or_404(
        Product,
        slug=slug
    )

    sort = request.GET.get(
        "sort",
        "recent"
    )

    base_reviews = ProductReview.objects.filter(
        product=product,
        is_approved=True
    ).prefetch_related(
        "images",
        "customer"
    )

    reviews = base_reviews

    if sort == "highest":

        reviews = reviews.order_by(
            "-rating",
            "-created_at"
        )

    elif sort == "lowest":

        reviews = reviews.order_by(
            "rating",
            "-created_at"
        )

    elif sort == "helpful":

        reviews = reviews.order_by(
            "-helpful_count",
            "-created_at"
        )

    else:

        reviews = reviews.order_by(
            "-created_at"
        )

    paginator = Paginator(
        reviews,
        10
    )

    page_obj = paginator.get_page(1)

    review_count = reviews.count()

    average_rating = (
        reviews.aggregate(
            Avg("rating")
        )["rating__avg"]
        or 0
    )



    rating_breakdown = {
    5: base_reviews.filter(rating=5).count(),
    4: base_reviews.filter(rating=4).count(),
    3: base_reviews.filter(rating=3).count(),
    2: base_reviews.filter(rating=2).count(),
    1: base_reviews.filter(rating=1).count(),
    }

    return render(
        request,
        "store/reviews_list.html",
        {
            "product": product,
            "reviews": page_obj.object_list,
            "page_obj": page_obj,
            "review_count": review_count,
            "average_rating": round(
                average_rating,
                1
            ),
            "selected_sort": sort,
            "rating_breakdown": rating_breakdown,
        }
    )


def load_more_reviews(request, slug):

    product = get_object_or_404(
        Product,
        slug=slug
    )

    page_number = request.GET.get(
        "page",
        1
    )

    sort = request.GET.get(
        "sort",
        "recent"
    )

    reviews = ProductReview.objects.filter(
        product=product,
        is_approved=True
    ).prefetch_related(
        "images",
        "customer"
    )

    if sort == "highest":

        reviews = reviews.order_by(
            "-rating",
            "-created_at"
        )

    elif sort == "lowest":

        reviews = reviews.order_by(
            "rating",
            "-created_at"
        )

    elif sort == "helpful":

        reviews = reviews.order_by(
            "-helpful_count",
            "-created_at"
        )

    else:

        reviews = reviews.order_by(
            "-created_at"
        )

    paginator = Paginator(
        reviews,
        10
    )

    page_obj = paginator.get_page(
        page_number
    )

    data = []

    for review in page_obj:

        images = []

        for image in review.images.all():

            images.append({
                "image": (
                    image.optimized.get("400")
                    if image.optimized
                    else image.original_image.url
                )
            })

        data.append({

            "id": review.id,

            "display_name":
                review.display_name,

            "city": review.city,

            "rating":
                review.rating,

            "review":
                review.review,

            "is_verified_buyer":
                review.is_verified_buyer,

            "helpful_count":
                review.helpful_count,

            "images":
                images,

            "created_at":
                review.created_at.strftime(
                    "%d %b %Y"
                )
        })

    return JsonResponse({

        "reviews": data,

        "has_next":
            page_obj.has_next(),

        "next_page":
            (
                page_obj.next_page_number()
                if page_obj.has_next()
                else None
            )
    })