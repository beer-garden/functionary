import django_filters
import django_tables2 as tables
from django.urls import reverse
from django.utils.html import format_html

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
        linkify=lambda record: reverse("ui:workflow-task", kwargs={"pk": record.id}),
        verbose_name="Workflow",
    )
    edit_button = tables.Column(
        accessor="id",
        verbose_name="",
    )

    class Meta(BaseMeta):
        model = Workflow
        fields = FIELDS

    def render_edit_button(self, value, record):
        return format_html(
            '<a class="fa fa-pencil-alt text-info" '
            f'role="button" '
            f'title="Edit Workflow" '
            f'href="{reverse("ui:workflow-detail", kwargs={"pk": record.id})}">'
            "</a>"
        )
