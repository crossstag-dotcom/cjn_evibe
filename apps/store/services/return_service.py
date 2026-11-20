# update return status based on returned quantity
def update_return_status(order):

    total_ordered = 0
    total_returned = 0

    for item in order.items.all():
        total_ordered += item.quantity
        total_returned += item.returned_quantity

    if total_returned == 0:
        order.return_status = "NONE"

    elif total_returned < total_ordered:
        order.return_status = "PARTIAL_RETURNED"

    else:
        order.return_status = "FULLY_RETURNED"

    order.save()