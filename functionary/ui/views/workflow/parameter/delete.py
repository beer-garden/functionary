import json

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from core.models import WorkflowParameter
from ui.tables.workflow_parameter import WorflowParameterTable
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
        workflow = parameter.workflow
        parameter.delete()

        messages.success(request, "Workflow saved.")
        context = {}
        if not workflow.parameters.exists():
            context = {
                "parameter_table": WorflowParameterTable([]),
                "workflow": workflow,
            }
            response = render(
                request, "partials/workflows/parameter_list.html", context
            )
            response["HX-Retarget"] = "#tableParameter"
            response["HX-Trigger"] = json.dumps({"showMessages": {}})
            return response

        return HttpResponse(
            headers={
                "HX-Trigger": json.dumps({"showMessages": {}}),
            },
        )
