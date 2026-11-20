"""Record traceable receipts without modifying the existing product/stock schema."""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("store", "0058_finishingbatch_reworkticket_finishingbatchsize_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="FinishedGoodsReceipt",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("quantity", models.PositiveIntegerField()),
                ("reference", models.CharField(max_length=100, unique=True)),
                ("posted_at", models.DateTimeField(auto_now_add=True)),
                ("finishing_size", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="goods_receipt", to="store.finishingbatchsize")),
                ("variant", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="manufacturing_receipts", to="store.productvariant")),
                ("warehouse", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="manufacturing_receipts", to="store.warehouse")),
                ("stock_movement", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="finished_goods_receipt", to="store.stockmovement")),
                ("posted_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="finished_goods_receipts", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddConstraint(
            model_name="finishedgoodsreceipt",
            constraint=models.CheckConstraint(condition=models.Q(("quantity__gt", 0)), name="fg_receipt_quantity_positive"),
        ),
    ]
