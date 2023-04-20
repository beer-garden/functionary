import django_filters
import django_tables2 as tables
from django.urls import reverse
from django.utils.html import format_html

from core.models import Function
from ui.tables.meta import BaseMeta

FIELDS = ("display_name", "summary")


class FunctionFilter(django_filters.FilterSet):
    display_name = django_filters.Filter(label="Function", lookup_expr="icontains")
    package = django_filters.Filter(
        field_name="package__display_name", label="Package", lookup_expr="icontains"
    )


class FunctionTable(tables.Table):
    display_name = tables.Column(
        linkify=lambda record: reverse("ui:function-detail", kwargs={"pk": record.id}),
        verbose_name="Function",
        orderable=True,
    )

    def render_display_name(self, value, record):
        return format_html(
            "<span title='Package: {package}' aria-label='{value}, from package "
            "{package}'>{value}<span class='text-muted ms-2 fs-8'>"
            "<span class='me-2'>:</span>{package}</span></span>",
            package=record.package.display_name,
            value=value,
        )

    class Meta(BaseMeta):
        model = Function
        fields = FIELDS
        empty_text = "No functions found"
