import django_filters
import django_tables2 as tables
from django.urls import reverse
from django.utils.html import format_html

from core.models import Function
from ui.tables.meta import BaseMeta

FIELDS = ("name", "summary")


class FunctionFilter(django_filters.FilterSet):
    name = django_filters.Filter(label="Function", lookup_expr="startswith")
    package = django_filters.Filter(
        field_name="package__name", label="Package", lookup_expr="startswith"
    )


class FunctionTable(tables.Table):
    name = tables.Column(
        linkify=lambda record: reverse("ui:function-detail", kwargs={"pk": record.id}),
        verbose_name="Function",
    )

    def render_name(self, value, record):
        return format_html(
            "<span title='Package: {}'>{}<span class='text-muted ms-2 fs-8'>"
            + "<span class='me-2'>:</span>{}</span></span>",
            record.package,
            value,
            record.package,
        )

    class Meta(BaseMeta):
        model = Function
        fields = FIELDS
