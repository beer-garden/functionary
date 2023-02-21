import django_filters
import django_tables2 as tables
from django.urls import reverse

from core.models import Function
from ui.tables.meta import BaseMeta

FIELDS = ("name", "package", "summary")


class FunctionFilter(django_filters.FilterSet):
    package = django_filters.Filter(field_name="package__name", label="Package")

    class Meta:
        model = Function
        fields = FIELDS


class FunctionTable(tables.Table):
    name = tables.Column(
        linkify=lambda record: reverse("ui:function-detail", kwargs={"pk": record.id}),
        attrs={"a": {"class": "text-decoration-none"}},
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
