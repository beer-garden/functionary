import django_filters
import django_tables2 as tables
from django.urls import reverse

from builder.models import Build
from ui.tables import DATETIME_FORMAT
from ui.tables.filters import DateTimeFilter
from ui.tables.meta import BaseMeta

FIELDS = ("package", "status", "creator", "created_at")


class BuildFilter(django_filters.FilterSet):
    package = django_filters.Filter(
        field_name="package__display_name", label="Package", lookup_expr="icontains"
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
        model = Build
        fields = FIELDS
        exclude = "created_at"


class BuildTable(tables.Table):
    package = tables.Column(
        linkify=lambda record: reverse("ui:build-detail", kwargs={"pk": record.id}),
        verbose_name="Package",
        accessor="package__display_name",
    )
    created_at = tables.DateTimeColumn(
        format=DATETIME_FORMAT,
    )

    class Meta(BaseMeta):
        model = Build
        fields = FIELDS
        orderable = True
        empty_text = "No builds found"
