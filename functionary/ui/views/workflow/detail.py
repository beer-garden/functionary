from core.models import Workflow
from ui.views.generic import PermissionedDetailView


class WorkflowDetailView(PermissionedDetailView):
    "Detail view for the Workflow model"

    model = Workflow
