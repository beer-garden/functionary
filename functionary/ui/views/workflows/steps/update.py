from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import UpdateView
from django_htmx.http import HttpResponseClientRedirect

from core.auth import Permission
from core.models import Function, WorkflowStep
from ui.forms import TaskParameterTemplateForm, WorkflowStepUpdateForm


class WorkflowStepUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Update view for WorkflowStep model"""

    model = WorkflowStep
    form_class = WorkflowStepUpdateForm
    template_name = WorkflowStepUpdateForm.template_name

    def get_context_data(self, **kwargs):
        """Custom context"""
        context = super().get_context_data(**kwargs)
        context["parameter_form"] = TaskParameterTemplateForm(
            self.get_object().function, initial=self.object.parameter_template
        )

        return context

    def get_form_kwargs(self):
        """Setup kwargs for form instantiation"""
        kwargs = super().get_form_kwargs()
        kwargs["environment"] = self.request.session["environment_id"]

        return kwargs

    def post(self, request, workflow_pk, pk):
        """Handle WorkflowStepForm submission"""
        # Various parent class calls require the object be set
        self.object = self.get_object()

        function = Function.objects.get(id=self.request.POST.get("function"))
        parameter_form = TaskParameterTemplateForm(
            function=function, data=self.request.POST
        )
        step_form = self.get_form()

        if step_form.is_valid() and parameter_form.is_valid():
            step_form.instance.parameter_template = parameter_form.parameter_template
            step = step_form.save()

            success_url = reverse("ui:workflow-detail", kwargs={"pk": step.workflow.pk})

            return HttpResponseClientRedirect(success_url)
        else:
            context = self.get_context_data()
            context["parameter_form"] = parameter_form

            return render(self.request, self.template_name, context)

    def test_func(self):
        """Permission check for view access"""
        step = self.get_object()

        return self.request.user.has_perm(
            Permission.WORKFLOW_UPDATE, step.workflow.environment
        )
