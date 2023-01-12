from core.auth import Permission
from core.models import Environment, Workflow
from ui.views.view_base import PermissionedEnvironmentListView

PAGINATION_AMOUNT = 10


class WorkflowListView(PermissionedEnvironmentListView):
    """List view for the Workflow model"""

    model = Workflow
    queryset = Workflow.objects.select_related("creator").all()
    order_by_fields = ["name"]
    paginate_by = PAGINATION_AMOUNT

    def get_context_data(self):
        environment_id = self.request.session.get("environment_id")
        environment = Environment.objects.get(id=environment_id)

        context = super().get_context_data()
        context["user_has_workflow_create"] = self.request.user.has_perm(
            Permission.WORKFLOW_CREATE, environment
        )

        return context
