import django_filters
import django_tables2 as tables
from django.urls import reverse

from core.models import Package
from ui.tables.meta import BaseMeta

FIELDS = ("display_name", "summary")


class PackageFilter(django_filters.FilterSet):
    display_name = django_filters.Filter(label="Package", lookup_expr="icontains")


class PackageTable(tables.Table):
    display_name = tables.Column(
        linkify=lambda record: reverse("ui:package-detail", kwargs={"pk": record.id}),
        verbose_name="Package",
        orderable=True,
    )

    class Meta(BaseMeta):
        model = Package
        fields = FIELDS
        empty_text = "No packages found"
