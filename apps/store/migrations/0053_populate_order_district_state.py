from django.db import migrations


def populate_district_state(apps, schema_editor):
    Order = apps.get_model("store", "Order")
    Pincode = apps.get_model("store", "Pincode")

    orders = Order.objects.filter(district__isnull=True)

    for order in orders:
        pin = (
            Pincode.objects
            .filter(pincode=order.pincode)
            .first()
        )

        if pin:
            order.district = pin.district
            order.state = pin.state
            order.save(update_fields=["district", "state"])


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0052_order_district_order_state"),
    ]

    operations = [
        migrations.RunPython(
            populate_district_state,
            migrations.RunPython.noop,
        ),
    ]