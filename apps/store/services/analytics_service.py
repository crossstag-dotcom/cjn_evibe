from django.db.models import Sum, Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta
from apps.store.models import Order, OrderItem, Refund, ReturnRequest, ProductVariant
from apps.analytics.models import ProductView




def get_revenue_today():
    today = timezone.localdate()

    revenue = (
        Order.objects.filter(
            delivered_at__date=today,
            status="DELIVERED"
        ).aggregate(total=Sum("total_amount"))["total"] or 0
    )

    return revenue


def get_orders_today():
    today = timezone.now().date()

    return Order.objects.filter(
        created_at__date=today
    ).count()


def get_pending_orders():
    return Order.objects.filter(
        status__in=["CREATED", "PAID", "PROCESSING", "PACKED"]
    ).count()


def get_in_transit_orders():
    return Order.objects.filter(
        status__in=["SHIPPED", "OUT_FOR_DELIVERY"]
    ).count()


def get_returns_count():
    return ReturnRequest.objects.count()


def get_refunds_total():
    return (
        Refund.objects.filter(status="SUCCESS")
        .aggregate(total=Sum("amount"))["total"] or 0
    )


def get_top_products(limit=10):

    return (
        OrderItem.objects.values("product__name")
        .annotate(total_sold=Sum("quantity"))
        .order_by("-total_sold")[:limit]
    )


def get_low_stock_products():

    return ProductVariant.objects.filter(
        stock__lt=5
    ).select_related("product")

def get_orders_trend(days=7):

    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days - 1)

    data = (
        Order.objects.filter(created_at__date__range=(start_date, end_date))
        .values("created_at__date")
        .annotate(count=Count("id"))
        .order_by("created_at__date")
    )

    trend = {}

    for i in range(days):
        date = start_date + timedelta(days=i)
        trend[date] = 0

    for row in data:
        trend[row["created_at__date"]] = row["count"]

    labels = [d.strftime("%d %b") for d in trend.keys()]
    values = list(trend.values())

    return labels, values

def get_order_status_distribution():

    data = (
        Order.objects
        .values("status")
        .annotate(total=Count("id"))
        .order_by()
    )

    labels = []
    values = []

    for row in data:
        labels.append(row["status"])
        values.append(row["total"])

    return labels, values

def get_revenue_trend(days=7):

    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days - 1)

    data = (
        Order.objects.filter(
            delivered_at__date__range=(start_date, end_date),
            status="DELIVERED"   # ✅ only completed revenue
        )
        .values("delivered_at__date")
        .annotate(total=Sum("total_amount"))
        .order_by("delivered_at__date")
    )

    trend = {}

    for i in range(days):
        date = start_date + timedelta(days=i)
        trend[date] = 0

    for row in data:
        trend[row["delivered_at__date"]] = float(row["total"] or 0)

    labels = [d.strftime("%d %b") for d in trend.keys()]
    values = list(trend.values())

    return labels, values

# Get product views trend for last N days
def get_product_views_trend(days=7):

    today = timezone.now().date()
    start_date = today - timedelta(days=days - 1)

    data = (
        ProductView.objects
        .filter(created_at__date__range=(start_date, today))
        .annotate(date=TruncDate("created_at"))
        .values("date")
        .annotate(total_views=Count("id"))
        .order_by("date")
    )

    # Fill missing days
    date_map = {item["date"]: item["total_views"] for item in data}

    labels = []
    values = []

    for i in range(days):
        day = start_date + timedelta(days=i)
        labels.append(day.strftime("%b %d"))
        values.append(date_map.get(day, 0))

    return labels, values


def get_daily_product_interest():
    """
    Date-wise grouped product views

    Example:
    25 Apr
        Cargo Pant → 3
        Black Denim → 2
    """

    data = (
        ProductView.objects
        .annotate(view_date=TruncDate("created_at"))
        .values(
            "view_date",
            "product__id",
            "product__name"
        )
        .annotate(
            total_views=Count("id")
        )
        .order_by(
            "-view_date",
            "-total_views"
        )
    )

    grouped_data = {}

    for item in data:
        date_key = item["view_date"]

        if date_key not in grouped_data:
            grouped_data[date_key] = []

        grouped_data[date_key].append({
            "product_id": item["product__id"],
            "product_name": item["product__name"],
            "total_views": item["total_views"]
        })

    return grouped_data

def get_product_drilldown(product_id, selected_date):
    """
    Product + Date based drilldown

    Returns:
    - city summary
    - session details
    """

    queryset = ProductView.objects.filter(
        product_id=product_id,
        created_at__date=selected_date
    )

    city_summary = (
        queryset
        .values("city")
        .annotate(total_views=Count("id"))
        .order_by("-total_views")
    )

    session_details = queryset.order_by("-created_at")

    product_name = None

    first_item = queryset.first()
    if first_item:
        product_name = first_item.product.name

    return {
        "product_name": product_name,
        "selected_date": selected_date,
        "city_summary": city_summary,
        "session_details": session_details
    }


def get_views_vs_orders():
    """
    Compare Product Views vs Actual Orders

    Returns:
    Product
    Views
    Orders
    Conversion %
    """

    # Total views grouped by product
    view_data = (
        ProductView.objects
        .values("product__id", "product__name")
        .annotate(total_views=Count("id"))
    )

    # Total ordered quantity grouped by product
    order_data = (
        OrderItem.objects
        .values("product__id")
        .annotate(total_orders=Sum("quantity"))
    )

    order_map = {
        item["product__id"]: item["total_orders"]
        for item in order_data
    }

    final_data = []

    for item in view_data:
        product_id = item["product__id"]
        total_views = item["total_views"]
        total_orders = order_map.get(product_id, 0)

        conversion = 0

        if total_views > 0:
            conversion = round(
                (total_orders / total_views) * 100,
                2
            )

        final_data.append({
            "product_name": item["product__name"],
            "total_views": total_views,
            "total_orders": total_orders,
            "conversion": conversion
        })

    final_data.sort(
        key=lambda x: x["conversion"],
        reverse=True
    )

    return final_data

def get_abandoned_checkouts():
    """
    Payment Drop-offs

    ONLINE payment selected
    but payment not completed

    Excludes COD orders
    """

    abandoned_orders = (
        Order.objects
        .filter(
            payment_method="ONLINE",
            status="CREATED"
        )
        .prefetch_related("items__product")
        .order_by("-created_at")
    )

    final_data = []

    for order in abandoned_orders:

        product_names = []

        for item in order.items.all():
            product_names.append(item.product.name)

        final_data.append({
            "customer_name": order.customer_name,
            "phone": order.phone,
            "city": order.city,
            "total_amount": order.total_amount,
            "products": product_names,
            "status": order.status,
            "created_at": order.created_at
        })

    return final_data


def get_dead_products():
    """
    Dead Products Report

    Rule:
    Product age >= 30 days
    Views < 20
    Orders < 3
    """

    from apps.store.models import Product, OrderItem

    cutoff_date = timezone.now() - timedelta(days=30)

    # Only products older than 30 days
    old_products = Product.objects.filter(
        created_at__lte=cutoff_date
    )

    # Views grouped
    view_data = (
        ProductView.objects
        .filter(product__in=old_products)
        .values("product__id", "product__name")
        .annotate(total_views=Count("id"))
    )

    # Orders grouped
    order_data = (
        OrderItem.objects
        .filter(product__in=old_products)
        .values("product__id")
        .annotate(total_orders=Sum("quantity"))
    )

    order_map = {
        item["product__id"]: item["total_orders"]
        for item in order_data
    }

    final_data = []

    for item in view_data:
        product_id = item["product__id"]
        total_views = item["total_views"]
        total_orders = order_map.get(product_id, 0)

        if total_views < 20 and total_orders < 3:
            final_data.append({
                "product_name": item["product__name"],
                "total_views": total_views,
                "total_orders": total_orders
            })

    final_data.sort(
        key=lambda x: (x["total_orders"], x["total_views"])
    )

    return final_data



def get_city_wise_revenue_intelligence(days=30):
    """
    City + Product Revenue Intelligence

    Metrics:
    - Views
    - Orders
    - Conversion %
    - Payment Drop-Offs

    Grouped by:
    City -> Product
    """

    from apps.store.models import OrderItem

    # Time filter
    if days == "all":
        view_queryset = ProductView.objects.all()
        order_queryset = Order.objects.all()
    else:
        cutoff_date = timezone.now() - timedelta(days=int(days))

        view_queryset = ProductView.objects.filter(
            created_at__gte=cutoff_date
        )

        order_queryset = Order.objects.filter(
            created_at__gte=cutoff_date
        )

    # Product views grouped by city + product
    view_data = (
        view_queryset
        .values(
            "city",
            "product__id",
            "product__name"
        )
        .annotate(total_views=Count("id"))
    )

    # Orders grouped by city + product
    order_data = (
        OrderItem.objects
        .filter(
            order__in=order_queryset
        )
        .values(
            "order__city",
            "product__id"
        )
        .annotate(total_orders=Sum("quantity"))
    )

    # Payment drop-offs
    dropoff_data = (
        order_queryset
        .filter(
            payment_method="ONLINE",
            status="CREATED"
        )
        .values(
            "city",
            "items__product__id"
        )
        .annotate(total_dropoffs=Count("id"))
    )

    order_map = {
        (
            item["order__city"],
            item["product__id"]
        ): item["total_orders"]
        for item in order_data
    }

    dropoff_map = {
        (
            item["city"],
            item["items__product__id"]
        ): item["total_dropoffs"]
        for item in dropoff_data
    }

    final_data = {}

    for item in view_data:
        city = item["city"] or "Unknown"
        product_id = item["product__id"]
        product_name = item["product__name"]
        total_views = item["total_views"]

        total_orders = order_map.get(
            (city, product_id),
            0
        )

        total_dropoffs = dropoff_map.get(
            (city, product_id),
            0
        )

        conversion = 0

        if total_views > 0:
            conversion = round(
                (total_orders / total_views) * 100,
                2
            )

        # Business insight
        if total_views >= 50 and total_dropoffs >= 10:
            insight = "Strong interest, payment issue"

        elif conversion >= 30:
            insight = "Excellent performer"

        elif total_orders <= 2:
            insight = "Weak product"

        else:
            insight = "Needs observation"

        if city not in final_data:
            final_data[city] = []

        final_data[city].append({
            "product_name": product_name,
            "views": total_views,
            "orders": total_orders,
            "conversion": conversion,
            "dropoffs": total_dropoffs,
            "insight": insight
        })

    return final_data