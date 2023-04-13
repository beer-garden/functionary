import django_filters
import django_tables2 as tables
from django.urls import reverse
from django.utils.html import format_html

from core.models.scheduled_task import ScheduledTask
from ui.tables import DATETIME_FORMAT
from ui.tables.meta import BaseMeta

FIELDS = ("name", "function", "last_run", "schedule", "status")


class ScheduledTaskFilter(django_filters.FilterSet):
    name = django_filters.Filter(label="Name", lookup_expr="startswith")
    function = django_filters.Filter(
        field_name="function__name", label="Function", lookup_expr="startswith"
    )

    class Meta:
        model = ScheduledTask
        fields = FIELDS
        exclude = ("schedule", "last_run")


def generateLastRunUrl(record):
    if record.most_recent_task:
        return reverse("ui:task-detail", kwargs={"pk": record.most_recent_task})
    return None


class ScheduledTaskTable(tables.Table):
    name = tables.Column(
        linkify=lambda record: reverse(
            "ui:scheduledtask-detail", kwargs={"pk": record.id}
        ),
    )
    function = tables.Column(accessor="function__name", verbose_name="Function")
    last_run = tables.DateTimeColumn(
        accessor="most_recent_task__created_at",
        verbose_name="Last Run",
        linkify=lambda record: generateLastRunUrl(record),
        format=DATETIME_FORMAT,
    )
    schedule = tables.Column(
        accessor="periodic_task__crontab", verbose_name="Schedule", orderable=False
    )
    edit_button = tables.Column(
        accessor="id",
        orderable=False,
        verbose_name="",
    )

    class Meta(BaseMeta):
        model = ScheduledTask
        fields = FIELDS
        orderable = True

    def render_edit_button(self, value, record):
        return format_html(
            '<a class="fa fa-pencil-alt text-info" role="button" title="Edit Schedule" '
            f'href="{reverse("ui:scheduledtask-update", kwargs={"pk": record.id})}">'
            "</a>"
        )

    def render_schedule(self, value):
        return format_html(
            "<span tabindex='0' data-bs-toggle='popover' data-bs-trigger='hover focus' "
            + "data-bs-content='{}'>{}<i class='fa fa-xs fa-fw fa-info-circle text-info"
            + " ms-2'></i><span class='visually-hidden'>{}</span></span>",
            value.human_readable,
            value,
            value.human_readable,
        )
