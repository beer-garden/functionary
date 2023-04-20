from django.urls import reverse

from core.models import Workflow
from ui.tables.workflow import WorkflowFilter, WorkflowTable
from ui.views.generic import PermissionedListView


class WorkflowListView(PermissionedListView):
    """List view for the Workflow model"""

    model = Workflow
    ordering = ["name"]
    table_class = WorkflowTable
    template_name = "core/workflow_list.html"
    filterset_class = WorkflowFilter
    queryset = Workflow.active_objects.select_related("environment", "creator")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [{"label": "Workflows"}]

        return context


class WorkflowArchiveListView(WorkflowListView):
    """List view for archived Workflows"""

    template_name = "core/workflow_archive.html"
    queryset = Workflow.objects.filter(active=False).select_related(
        "environment", "creator"
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"label": "Workflows", "url": reverse("ui:workflow-list")},
            {"label": "Archive"},
        ]

        return context
