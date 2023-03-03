import django_filters
import django_tables2 as tables
from django.urls import reverse

from core.models import Workflow
from ui.tables.meta import BaseMeta

FIELDS = ("name", "description", "creator")


class WorkflowFilter(django_filters.FilterSet):
    name = django_filters.Filter(label="Workflow", lookup_expr="startswith")
    creator = django_filters.Filter(
        field_name="creator__username", label="Creator", lookup_expr="startswith"
    )


class WorkflowTable(tables.Table):
    name = tables.Column(
        linkify=lambda record: reverse("ui:workflow-detail", kwargs={"pk": record.id}),
        attrs={"a": {"class": "text-decoration-none"}},
        verbose_name="Workflow",
    )

    class Meta(BaseMeta):
        model = Workflow
        fields = FIELDS
