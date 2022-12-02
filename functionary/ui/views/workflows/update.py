from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse
from django.views.generic import UpdateView
from django_htmx.http import HttpResponseClientRedirect

from core.auth import Permission
from core.models import Workflow


class WorkflowUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """View to handle updates of Workflow details"""

    model = Workflow
    template_name = "forms/workflows/workflow_edit.html"
    fields = ["name", "description"]

    def form_valid(self, form):
        form.save()
        success_url = reverse("ui:workflow-detail", kwargs={"pk": form.instance.pk})

        return HttpResponseClientRedirect(success_url)

    def test_func(self):
        workflow = self.get_object()

        return self.request.user.has_perm(
            Permission.WORKFLOW_UPDATE, workflow.environment
        )
