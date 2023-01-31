from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, render
from django.views.generic import View

from core.auth import Permission
from core.models import WorkflowStep
from core.utils.workflow import remove_step


class WorkflowStepDeleteView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Delete view for the WorkflowStep model"""

    def _get_object(self):
        return get_object_or_404(
            WorkflowStep,
            workflow__pk=self.kwargs.get("workflow_pk"),
            pk=self.kwargs.get("pk"),
        )

    def delete(self, request, workflow_pk, pk):
        step = self._get_object()
        context = {"workflow": step.workflow}
        remove_step(step)

        return render(request, "partials/workflows/step_list.html", context)

    def test_func(self):
        """Permission check for access to the view"""
        env = self._get_object().workflow.environment
        return self.request.user.has_perm(Permission.WORKFLOW_UPDATE, env)
