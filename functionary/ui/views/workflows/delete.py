from django.urls import reverse_lazy

from core.models import Workflow
from ui.views.generic import PermissionedDeleteView


class WorkflowDeleteView(PermissionedDeleteView):
    "Delete view for the Workflow model"

    model = Workflow
    success_url = reverse_lazy("ui:workflow-list")
