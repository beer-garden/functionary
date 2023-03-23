from core.auth import Permission
from core.models import Workflow
from ui.forms.tasks import TaskParameterForm
from ui.views.generic import PermissionedDetailView


class WorkflowTaskCreateView(PermissionedDetailView):
    """Task create view for Workflows"""

    model = Workflow
    template_name = "core/workflow_task.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        workflow = self.object
        env = workflow.environment

        all_vars = list(env.variables.values_list("name", flat=True))
        missing_variables = []

        for step in workflow.steps.all():
            missing_variables += [
                var for var in step.function.variables if var not in all_vars
            ]

        context["missing_variables"] = set(missing_variables)

        if self.request.user.has_perm(Permission.TASK_CREATE, env):
            context["form"] = TaskParameterForm(workflow)

        return context
