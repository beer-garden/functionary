from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse
from django.views.generic import CreateView
from django_htmx.http import HttpResponseClientRedirect

from core.auth import Permission
from core.models import Environment, Workflow


class WorkflowCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Create view for the Workflow model"""

    model = Workflow
    template_name = "forms/workflows/workflow_edit.html"
    fields = ["name", "description", "environment"]

    def form_valid(self, form):
        """Valid form handler"""
        form.instance.creator = self.request.user
        form.save()

        success_url = reverse("ui:workflow-detail", kwargs={"pk": form.instance.pk})

        return HttpResponseClientRedirect(success_url)

    def test_func(self):
        # On GET, the session environment is checked.
        # On POST, the actual environment value from the form is checked.
        environment_id = self.request.POST.get(
            "environment"
        ) or self.request.session.get("environment_id")
        environment = Environment.objects.get(id=environment_id)

        return self.request.user.has_perm(Permission.WORKFLOW_CREATE, environment)
