import django_tables2 as tables
from django.urls import reverse

from core.models import Workflow


class WorkflowTable(tables.Table):
    name = tables.Column(
        linkify=lambda record: reverse("ui:workflow-detail", kwargs={"pk": record.id}),
    )

    class Meta:
        model = Workflow
        fields = ("name", "description", "creator")
        attrs = {"class": "table is-striped is-hoverable is-fullwidth"}
