from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic import View

from core.auth import Permission
from core.models import WorkflowParameter


class WorkflowParameterDeleteView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Delete view for the WorkflowParameter model"""

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

    def test_func(self):
        """Permission check for access to the view"""
        env = self._get_object().workflow.environment
        return self.request.user.has_perm(Permission.WORKFLOW_UPDATE, env)
