import django_filters
import django_tables2 as tables
from django.urls import reverse

from core.models import Task
from ui.tables import DATETIME_FORMAT
from ui.tables.filters import DateTimeFilter
from ui.tables.meta import BaseMeta

FIELDS = ("function", "status", "creator", "created_at")


class TaskListFilter(django_filters.FilterSet):
    function = django_filters.Filter(
        field_name="function__name", label="Function", lookup_expr="startswith"
    )
    creator = django_filters.Filter(
        field_name="creator__username", label="Creator", lookup_expr="startswith"
    )
    created_at_min = DateTimeFilter(
        field_name="created_at",
        label="Created after",
        lookup_expr="gte",
    )
    created_at_max = DateTimeFilter(
        field_name="created_at",
        label="Created before",
        lookup_expr="lte",
    )

    class Meta:
        model = Task
        fields = FIELDS
        exclude = "created_at"


class TaskListTable(tables.Table):
    function = tables.Column(
        linkify=lambda record: reverse("ui:task-detail", kwargs={"pk": record.id}),
    )

    created_at = tables.DateTimeColumn(
        format=DATETIME_FORMAT,
    )

    class Meta(BaseMeta):
        model = Task
        fields = FIELDS
