"""Create size-wise QC records after processing custody migration."""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("store", "0056_processingbatch_processingbatchsize_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="QualityInspection",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("reference", models.CharField(max_length=80, unique=True)),
                ("status", models.CharField(choices=[("DRAFT", "Draft"), ("POSTED", "Posted")], default="DRAFT", max_length=12)),
                ("defect_notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("posted_at", models.DateTimeField(blank=True, null=True)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="quality_inspections_created", to=settings.AUTH_USER_MODEL)),
                ("posted_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="quality_inspections_posted", to=settings.AUTH_USER_MODEL)),
                ("processing_batch", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="quality_inspection", to="store.processingbatch")),
            ],
        ),
        migrations.CreateModel(
            name="QualityInspectionSize",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("size", models.CharField(max_length=12)),
                ("inspected_pieces", models.PositiveIntegerField()),
                ("approved_pieces", models.PositiveIntegerField()),
                ("rework_pieces", models.PositiveIntegerField()),
                ("rejected_pieces", models.PositiveIntegerField()),
                ("inspection", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="size_lines", to="store.qualityinspection")),
            ],
        ),
        migrations.AddConstraint(
            model_name="qualityinspectionsize",
            constraint=models.UniqueConstraint(fields=("inspection", "size"), name="unique_quality_inspection_size"),
        ),
        migrations.AddConstraint(
            model_name="qualityinspectionsize",
            constraint=models.CheckConstraint(
                condition=models.Q(("inspected_pieces", models.F("approved_pieces") + models.F("rework_pieces") + models.F("rejected_pieces"))),
                name="qc_outcomes_equal_inspected",
            ),
        ),
    ]
