from django.urls import reverse

from core.auth import Permission
from core.models import Workflow
from ui.forms.tasks import TaskMetadataForm, TaskParameterForm
from ui.views.generic import PermissionedDetailView


class WorkflowDetailView(PermissionedDetailView):
    """Workflow detail and task creation view"""

    model = Workflow
    template_name = "core/workflow_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        workflow = self.object
        env = workflow.environment
        breadcrumbs = [
            {"label": "Workflows", "url": reverse("ui:workflow-list")},
            {"label": workflow.display_name},
        ]
        if not workflow.active:
            breadcrumbs.insert(
                1,
                {
                    "label": "Archive",
                    "url": reverse("ui:workflow-archive-list"),
                },
            )
        context["breadcrumbs"] = breadcrumbs

        all_vars = list(env.variables.values_list("name", flat=True))
        missing_variables = []

        for step in workflow.steps.all():
            missing_variables += [
                var for var in step.tasked_object.variables if var not in all_vars
            ]

        context["missing_variables"] = set(missing_variables)

        if self.request.user.has_perm(Permission.TASK_CREATE, env):
            context["parameter_form"] = TaskParameterForm(
                tasked_object=workflow, creator=self.request.user
            )
            context["metadata_form"] = TaskMetadataForm()

        return context
