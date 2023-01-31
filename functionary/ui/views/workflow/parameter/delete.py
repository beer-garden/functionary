from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from core.models import WorkflowParameter
from ui.views.generic import PermissionedDeleteView


class WorkflowParameterDeleteView(PermissionedDeleteView):
    """Delete view for the WorkflowParameter model"""

    permissioned_model = "Workflow"

    def _get_object(self):
        return get_object_or_404(
            WorkflowParameter,
            workflow__pk=self.kwargs.get("workflow_pk"),
            pk=self.kwargs.get("pk"),
        )

    def delete(self, request, workflow_pk, pk):
        parameter = self._get_object()
        parameter.delete()

        return HttpResponse()
