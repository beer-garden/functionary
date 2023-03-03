import django_filters
import django_tables2 as tables
from django.urls import reverse

from core.models import Function
from ui.tables.meta import BaseMeta

FIELDS = ("name", "package", "summary")


class FunctionFilter(django_filters.FilterSet):
    name = django_filters.Filter(label="Function", lookup_expr="startswith")
    package = django_filters.Filter(
        field_name="package__name", label="Package", lookup_expr="startswith"
    )


class FunctionTable(tables.Table):
    name = tables.Column(
        linkify=lambda record: reverse("ui:function-detail", kwargs={"pk": record.id}),
        attrs={"a": {"class": "text-decoration-none"}},
        verbose_name="Function",
    )
    package = tables.Column(
        linkify=lambda record: reverse(
            "ui:package-detail", kwargs={"pk": record.package.id}
        ),
        attrs={"a": {"class": "text-decoration-none"}},
    )

    class Meta(BaseMeta):
        model = Function
        fields = FIELDS
