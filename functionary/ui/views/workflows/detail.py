from core.models import Workflow
from ui.views.view_base import PermissionedEnvironmentDetailView


class WorkflowDetailView(PermissionedEnvironmentDetailView):
    "Detail view for the Workflow model"

    model = Workflow
