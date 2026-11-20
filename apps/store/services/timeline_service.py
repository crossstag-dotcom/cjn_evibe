
from ..models import OrderTimeline
def log_order_event(order, event_type, message):

    OrderTimeline.objects.create(
        order=order,
        event_type=event_type,
        message=message
    )
