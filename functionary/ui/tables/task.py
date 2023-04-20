import django_filters
import django_tables2 as tables
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.forms.widgets import HiddenInput
from django.urls import reverse
from django.utils.html import format_html

from core.models import Function, Task, Workflow
from ui.tables import DATETIME_FORMAT
from ui.tables.filters import DateTimeFilter
from ui.tables.meta import BaseMeta

FUNCTION = Function.__name__.lower()
WORKFLOW = Workflow.__name__.lower()
TYPE_CHOICES = (
    (FUNCTION, FUNCTION),
    (WORKFLOW, WORKFLOW),
)


class TaskListFilter(django_filters.FilterSet):
    type = django_filters.ChoiceFilter(
        field_name="tasked_type__model", label="Type", choices=TYPE_CHOICES
    )
    name = django_filters.Filter(method="filter_name", label="Name")
    creator = django_filters.Filter(field_name="creator__username", label="Creator")
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
    scheduled_task_id = django_filters.Filter(
        field_name="scheduled_task__id",
        label="Scheduled Task",
        widget=HiddenInput(),
    )
    schedule_name = django_filters.Filter(
        field_name="scheduled_task__name", label="Schedule", lookup_expr="startswith"
    )
    comment = django_filters.Filter(label="Comment", method="filter_comment")

    class Meta:
        model = Task
        fields = (
            "type",
            "name",
            "status",
            "creator",
            "created_at_min",
            "created_at_max",
            "schedule_name",
            "comment",
        )

    def filter_name(self, queryset, field_name, value):
        """Generate queryset for filtering by tasked_object name"""
        function_ids = Function.objects.filter(
            display_name__icontains=value
        ).values_list("id", flat=True)
        workflow_ids = Workflow.objects.filter(name__icontains=value).values_list(
            "id", flat=True
        )
        function_ct = ContentType.objects.get_for_model(Function)
        workflow_ct = ContentType.objects.get_for_model(Workflow)

        function_filter = Q(tasked_type=function_ct, tasked_id__in=function_ids)
        workflow_filter = Q(tasked_type=workflow_ct, tasked_id__in=workflow_ids)

        return queryset.filter(function_filter | workflow_filter)

    def filter_comment(self, queryset, field_name, value):
        """Generate queryset for filtering by comment"""
        return queryset.filter(comment__icontains=value)


class TaskListTable(tables.Table):
    name = tables.Column(
        accessor="tasked_object__display_name",
        verbose_name="Name",
        linkify=lambda record: reverse("ui:task-detail", kwargs={"pk": record.id}),
    )
    created_at = tables.DateTimeColumn(
        format=DATETIME_FORMAT, verbose_name="Created", orderable=True
    )
    comment = tables.Column(default="")

    def render_name(self, value, record):
        icon = "fa-cube" if record.tasked_type.name == "function" else "fa-diagram-next"
        return format_html(
            "<span title='{taskType}' aria-label='{taskName}, a {taskType}'><i class="
            "'fa {icon} fa-fw me-2'></i>{taskName}</span>",
            taskType=record.tasked_type.name.capitalize(),
            taskName=record.tasked_object.display_name,
            icon=icon,
        )

    def render_comment(self, value, record):
        comment = value.strip()

        return format_html(
            "<span tabindex='0'"
            "class='line-clamp text-wrap'"
            "data-bs-toggle='popover' "
            "data-bs-container='#table-list-block' "
            "data-bs-trigger='hover focus' "
            "data-bs-content='{comment}'>{comment}"
            "</span>",
            comment=comment,
        )

    def _render_created_via_scheduled_task(self, value, record):
        """Helper for rendering the scheduled task that spawned the task"""
        link = reverse(
            "ui:scheduledtask-detail", kwargs={"pk": record.scheduled_task.id}
        )
        return format_html(
            "{value}<span class='text-muted ms-2 fs-8' title='Scheduled Task'><span "
            "class='me-2'>via</span><a href='{link}' aria-label='via Scheduled Task "
            "{name}'><i class='fa fa-clock me-2'></i>{name}</a></span>",
            value=value,
            link=link,
            name=record.scheduled_task.display_name,
        )

    def _render_created_via_workflow(self, value, record):
        """Helper for rendering the workflow that spawned the task"""
        link = reverse(
            "ui:task-detail", kwargs={"pk": record.workflow_run_step.workflow_task.id}
        )
        return format_html(
            "{value}<span class='text-muted ms-2 fs-8' title='Workflow'><span class='"
            "me-2'>via</span><a href='{link}' aria-label='via Workflow {wfName}'>"
            "<i class='fa fa-diagram-next me-2'></i>{wfName}</a></span>",
            wfName=record.workflow_run_step.workflow_task.workflow.display_name,
            value=value,
            link=link,
        )

    def render_creator(self, value, record):
        if record.scheduled_task:
            return self._render_created_via_scheduled_task(value, record)
        elif hasattr(record, "workflow_run_step"):
            return self._render_created_via_workflow(value, record)
        else:
            return value

    class Meta(BaseMeta):
        model = Task
        fields = ("name", "status", "creator", "comment", "created_at")
        empty_text = "No tasking found"
