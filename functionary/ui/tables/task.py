import django_filters
import django_tables2 as tables
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
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
        model = Task
        fields = (
            "type",
            "name",
            "status",
            "creator",
            "created_at_min",
            "created_at_max",
        )

    def filter_name(self, queryset, name, value):
        """Generate queryset for filtering by tasked_object name"""
        function_ids = Function.objects.filter(name__startswith=value).values_list(
            "id", flat=True
        )
        workflow_ids = Workflow.objects.filter(name__startswith=value).values_list(
            "id", flat=True
        )
        function_ct = ContentType.objects.get_for_model(Function)
        workflow_ct = ContentType.objects.get_for_model(Workflow)

        function_filter = Q(tasked_type=function_ct, tasked_id__in=function_ids)
        workflow_filter = Q(tasked_type=workflow_ct, tasked_id__in=workflow_ids)

        return queryset.filter(function_filter | workflow_filter)


class TaskListTable(tables.Table):
    name = tables.Column(
        accessor="tasked_object__name",
        verbose_name="Name",
        linkify=lambda record: reverse("ui:task-detail", kwargs={"pk": record.id}),
    )
    created_at = tables.DateTimeColumn(
        format=DATETIME_FORMAT, verbose_name="Created", orderable=True
    )

    def render_name(self, value, record):
        icon = "fa-cube" if record.tasked_type.name == "function" else "fa-diagram-next"
        return format_html(
            "<i class='fa {} fa-fw me-2' title='{}'></i>{}",
            icon,
            record.tasked_type.name.capitalize(),
            record.tasked_object.name,
        )

    class Meta(BaseMeta):
        model = Task
        fields = ("name", "status", "creator", "created_at")
        orderable = False
