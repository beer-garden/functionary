import django_filters
import django_tables2 as tables
from django.urls import reverse

from core.models import Package
from ui.tables.meta import BaseMeta

FIELDS = ("name", "summary")


class PackageFilter(django_filters.FilterSet):
    name = django_filters.Filter(label="Package", lookup_expr="startswith")


class PackageTable(tables.Table):
    name = tables.Column(
        linkify=lambda record: reverse("ui:package-detail", kwargs={"pk": record.id}),
        verbose_name="Package",
        orderable=True,
    )

    class Meta(BaseMeta):
        model = Package
        fields = FIELDS
