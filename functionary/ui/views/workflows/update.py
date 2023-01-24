from django.urls import reverse
from django_htmx.http import HttpResponseClientRedirect

from core.models import Workflow
from ui.views.generic import PermissionedUpdateView


class WorkflowUpdateView(PermissionedUpdateView):
    """View to handle updates of Workflow details"""

    model = Workflow
    template_name = "forms/workflows/workflow_edit.html"
    fields = ["name", "description"]

    def form_valid(self, form):
        form.save()
        success_url = reverse("ui:workflow-detail", kwargs={"pk": form.instance.pk})

        return HttpResponseClientRedirect(success_url)
