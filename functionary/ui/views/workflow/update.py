import json

from django.urls import reverse
from django_htmx.http import HttpResponseClientRedirect

from core.models import Workflow
from ui.views.generic import PermissionedUpdateView


class WorkflowUpdateView(PermissionedUpdateView):
    """View to handle updates of Workflow details"""

    model = Workflow
    template_name = "forms/workflow/workflow_edit.html"
    fields = ["name", "description"]

    def form_valid(self, form):
        form.save()
        workflow: Workflow = self.get_object()
        success_url = reverse("ui:workflow-update", kwargs={"pk": workflow.id})

        return HttpResponseClientRedirect(
            success_url,
            headers={
                "HX-Trigger": json.dumps(
                    {"showMessages": [{"level": "success", "msg": "Waveform saved."}]}
                ),
            },
        )
