# Generated by Django 4.1.3 on 2022-11-23 00:00

import uuid

import django.core.serializers.json
import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0006_scheduledtask_task_scheduled_task_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="Workflow",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("name", models.CharField(max_length=64)),
                ("description", models.TextField(null=True)),
                ("schema", models.JSONField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "creator",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "environment",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="core.environment",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="WorkflowRun",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("PENDING", "Pending"),
                            ("IN_PROGRESS", "In Progress"),
                            ("COMPLETE", "Complete"),
                            ("ERROR", "Error"),
                        ],
                        default="PENDING",
                        max_length=16,
                    ),
                ),
                (
                    "parameters",
                    models.JSONField(
                        blank=True,
                        encoder=django.core.serializers.json.DjangoJSONEncoder,
                        null=True,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "creator",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "environment",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="core.environment",
                    ),
                ),
                (
                    "workflow",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="runs",
                        to="core.workflow",
                    ),
                ),
            ],
        ),
        migrations.AlterField(
            model_name="variable",
            name="name",
            field=models.CharField(
                max_length=255,
                validators=[
                    django.core.validators.RegexValidator(
                        message="Invalid variable name. Characters must be in [A-Z0-9_]",
                        regex="^[A-Z_][A-Z0-9_]*$",
                    )
                ],
            ),
        ),
        migrations.CreateModel(
            name="WorkflowStep",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        max_length=64,
                        validators=[
                            django.core.validators.RegexValidator(
                                message="Invalid step name. Only numbers, letters, and underscore are allowed.",
                                regex="^[a-zA-Z0-9_]+$",
                            )
                        ],
                    ),
                ),
                ("sequence", models.IntegerField()),
                ("parameter_template", models.TextField(blank=True, null=True)),
                (
                    "function",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="core.function"
                    ),
                ),
                (
                    "workflow",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="steps",
                        to="core.workflow",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="WorkflowRunStep",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "task",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="workflow_run_step",
                        to="core.task",
                    ),
                ),
                (
                    "workflow_run",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="steps",
                        to="core.workflowrun",
                    ),
                ),
                (
                    "workflow_step",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="core.workflowstep",
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="workflowstep",
            constraint=models.UniqueConstraint(
                fields=("workflow", "sequence"),
                name="ws_workflow_sequence_unique_together",
            ),
        ),
        migrations.AddConstraint(
            model_name="workflowstep",
            constraint=models.UniqueConstraint(
                fields=("workflow", "name"), name="ws_workflow_name_unique_together"
            ),
        ),
        migrations.AddIndex(
            model_name="workflowrun",
            index=models.Index(
                fields=["environment", "status"], name="wr_environment_status"
            ),
        ),
        migrations.AddIndex(
            model_name="workflowrun",
            index=models.Index(
                fields=["environment", "creator"], name="wr_environment_creator"
            ),
        ),
        migrations.AddIndex(
            model_name="workflowrun",
            index=models.Index(
                fields=["environment", "created_at"], name="wr_environment_created_at"
            ),
        ),
        migrations.AddIndex(
            model_name="workflowrun",
            index=models.Index(
                fields=["environment", "updated_at"], name="wr_environment_updated_at"
            ),
        ),
        migrations.AddIndex(
            model_name="workflow",
            index=models.Index(
                fields=["environment", "creator"], name="workflow_environment_creator"
            ),
        ),
        migrations.AddIndex(
            model_name="workflow",
            index=models.Index(
                fields=["environment", "created_at"], name="workflow_created_at"
            ),
        ),
        migrations.AddConstraint(
            model_name="workflow",
            constraint=models.UniqueConstraint(
                fields=("environment", "name"),
                name="workflow_environment_name_unique_together",
            ),
        ),
    ]
