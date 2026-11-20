"""Add optional SKU and colour identity without rewriting existing variants."""
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("store", "0059_finishedgoodsreceipt"),
    ]

    operations = [
        migrations.CreateModel(
            name="VariantIdentity",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("sku", models.CharField(max_length=100, unique=True)),
                ("colour", models.CharField(max_length=100)),
                ("article_code", models.CharField(max_length=100)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("variant", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="identity", to="store.productvariant")),
            ],
        ),
    ]
