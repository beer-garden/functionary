import django_filters
import django_tables2 as tables
from django.urls import reverse

from core.models import Workflow
from ui.tables.meta import BaseMeta

FIELDS = ("name", "description", "creator")


class WorkflowFilter(django_filters.FilterSet):
    creator = django_filters.Filter(field_name="creator__username", label="Creator")

    class Meta:
        model = Workflow
        fields = FIELDS
        exclude = "description"


class WorkflowTable(tables.Table):
    name = tables.Column(
        linkify=lambda record: reverse("ui:workflow-detail", kwargs={"pk": record.id}),
        attrs={"a": {"class": "text-decoration-none"}},
    )

    class Meta(BaseMeta):
        model = Workflow
        fields = FIELDS
