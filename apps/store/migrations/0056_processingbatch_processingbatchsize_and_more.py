# Generated for the EVIBE washing and processing custody workflow.
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("store", "0055_warehouse_cuttingorder_cuttingcompletion_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ProcessingBatch",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("reference", models.CharField(max_length=80, unique=True)),
                ("processor", models.CharField(max_length=160)),
                ("status", models.CharField(choices=[("ISSUED", "Sent for washing/processing"), ("RECEIVED", "Received from processing")], default="ISSUED", max_length=12)),
                ("issued_at", models.DateTimeField(auto_now_add=True)),
                ("received_at", models.DateTimeField(blank=True, null=True)),
                ("issued_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="processing_issues", to=settings.AUTH_USER_MODEL)),
                ("received_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="processing_receipts", to=settings.AUTH_USER_MODEL)),
                ("stitching_transfer", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="processing_batch", to="store.stitchingtransfer")),
            ],
        ),
        migrations.CreateModel(
            name="ProcessingBatchSize",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("size", models.CharField(max_length=12)),
                ("issued_pieces", models.PositiveIntegerField()),
                ("received_pieces", models.PositiveIntegerField(blank=True, null=True)),
                ("batch", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="size_lines", to="store.processingbatch")),
            ],
        ),
        migrations.AddConstraint(
            model_name="processingbatchsize",
            constraint=models.UniqueConstraint(fields=("batch", "size"), name="unique_processing_batch_size"),
        ),
        migrations.AddConstraint(
            model_name="processingbatchsize",
            constraint=models.CheckConstraint(condition=models.Q(("issued_pieces__gt", 0)), name="processing_issued_positive"),
        ),
        migrations.AddConstraint(
            model_name="processingbatchsize",
            constraint=models.CheckConstraint(condition=models.Q(("received_pieces__isnull", True), ("received_pieces__gte", 0), _connector="OR"), name="processing_received_nonnegative"),
        ),
    ]
