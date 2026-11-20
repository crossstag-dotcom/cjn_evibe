"""Finishing and rework custody records; no warehouse balance changes."""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("store", "0057_qualityinspection_qualityinspectionsize_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="FinishingBatch",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("reference", models.CharField(max_length=80, unique=True)),
                ("status", models.CharField(choices=[("OPEN", "In finishing"), ("COMPLETED", "Finishing completed")], default="OPEN", max_length=12)),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="finishing_batches_created", to=settings.AUTH_USER_MODEL)),
                ("completed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="finishing_batches_completed", to=settings.AUTH_USER_MODEL)),
                ("inspection", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="finishing_batch", to="store.qualityinspection")),
            ],
        ),
        migrations.CreateModel(
            name="FinishingBatchSize",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("size", models.CharField(max_length=12)),
                ("approved_from_qc", models.PositiveIntegerField()),
                ("finished_pieces", models.PositiveIntegerField(blank=True, null=True)),
                ("finishing_rework_pieces", models.PositiveIntegerField(blank=True, null=True)),
                ("batch", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="size_lines", to="store.finishingbatch")),
            ],
        ),
        migrations.CreateModel(
            name="ReworkTicket",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("reference", models.CharField(max_length=80, unique=True)),
                ("size", models.CharField(max_length=12)),
                ("pieces", models.PositiveIntegerField()),
                ("reason", models.CharField(max_length=240)),
                ("status", models.CharField(choices=[("OPEN", "Awaiting repair"), ("REPAIRED", "Repaired; awaiting QC")], default="OPEN", max_length=12)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("repaired_at", models.DateTimeField(blank=True, null=True)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="rework_tickets_created", to=settings.AUTH_USER_MODEL)),
                ("repaired_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="rework_tickets_repaired", to=settings.AUTH_USER_MODEL)),
                ("inspection", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="rework_tickets", to="store.qualityinspection")),
            ],
        ),
        migrations.AddConstraint(
            model_name="finishingbatchsize",
            constraint=models.UniqueConstraint(fields=("batch", "size"), name="unique_finishing_batch_size"),
        ),
        migrations.AddConstraint(
            model_name="finishingbatchsize",
            constraint=models.CheckConstraint(
                condition=models.Q(("finished_pieces__isnull", True), ("finished_pieces__lte", models.F("approved_from_qc")), _connector="OR"),
                name="finishing_not_above_qc_approved",
            ),
        ),
        migrations.AddConstraint(
            model_name="reworkticket",
            constraint=models.CheckConstraint(condition=models.Q(("pieces__gt", 0)), name="rework_ticket_pieces_positive"),
        ),
    ]
