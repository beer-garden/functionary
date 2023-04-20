from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseRedirect,
)
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.html import format_html
from django.views.decorators.http import require_GET, require_POST

from core.auth import Permission
from core.models import Environment, Function, Task, Workflow
from core.utils.tasking import start_task
from ui.forms.tasks import (
    TaskMetadataForm,
    TaskParameterForm,
    TaskParameterTemplateForm,
)
from ui.tables.function import FunctionFilter, FunctionTable

from .generic import PermissionedDetailView, PermissionedListView


class FunctionListView(PermissionedListView):
    model = Function
    ordering = ["package__display_name", "display_name"]
    table_class = FunctionTable
    filterset_class = FunctionFilter
    queryset = Function.active_objects.select_related("package")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [{"label": "Functions"}]

        return context


class FunctionDetailView(PermissionedDetailView):
    model = Function
    environment_through_field = "package"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related(
                "package", "package__environment", "package__environment__team"
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        function = self.object
        env = function.environment

        missing_variables = []
        if function.variables:
            all_vars = list(env.variables.values_list("name", flat=True))
            missing_variables = [
                var for var in function.variables if var not in all_vars
            ]

        context["missing_variables"] = missing_variables
        context["breadcrumbs"] = [
            {
                "label": "Functions",
                "url": reverse("ui:function-list"),
            },
            {
                "label": function.package.display_name,
                "url": reverse("ui:package-detail", kwargs={"pk": function.package.id}),
                "icon": format_html('<i class="fa fa-cubes"></i>'),
            },
            {"label": function.display_name},
        ]

        if self.request.user.has_perm(Permission.TASK_CREATE, env):
            context["parameter_form"] = TaskParameterForm(
                tasked_object=function, creator=self.request.user
            )
            context["metadata_form"] = TaskMetadataForm()

        return context


@require_POST
@login_required
def execute(request: HttpRequest) -> HttpResponse:
    status_code = None
    env = Environment.objects.get(id=request.session.get("environment_id"))

    if not request.user.has_perm(Permission.TASK_CREATE, env):
        return HttpResponseForbidden()

    data = request.POST

    if tasked_object_id := data.get("function_id"):
        tasked_object = get_object_or_404(
            Function, id=tasked_object_id, environment=env
        )
    elif tasked_object_id := data.get("workflow_id"):
        tasked_object = get_object_or_404(
            Workflow, id=tasked_object_id, environment=env
        )
    else:
        return HttpResponseBadRequest("function_id or workflow_id is required")

    parameter_form = TaskParameterForm(
        tasked_object=tasked_object, creator=request.user, data=data
    )

    metadata_form = TaskMetadataForm(data=data)

    if parameter_form.is_valid() and metadata_form.is_valid():
        # Clean the task fields before saving the Task
        task = None
        try:
            # Create the new Task, the validated parameters are in form.cleaned_data
            task = Task(
                environment=env,
                creator=request.user,
                tasked_object=tasked_object,
                parameters=parameter_form.cleaned_data,
                return_type=getattr(tasked_object, "return_type", None),
                **metadata_form.cleaned_data,
            )
            task.clean()
        except ValidationError:
            task = None
            status_code = 400
            parameter_form.add_error(
                None,
                ValidationError(
                    "The given parameters do not conform to function schema.",
                    code="invalid",
                ),
            )

        if task:
            start_task(task)

            # Redirect to the newly created task:
            return HttpResponseRedirect(reverse("ui:task-detail", args=(task.id,)))

    context = {}
    context["parameter_form"] = parameter_form
    context["metadata_form"] = metadata_form

    if isinstance(tasked_object, Function):
        context["function"] = tasked_object
        template = "core/function_detail.html"
    else:
        context["workflow"] = tasked_object
        template = "core/workflow_detail.html"

    return render(request, template, context, status=status_code)


@require_GET
@login_required
def function_parameters(request: HttpRequest) -> HttpResponse:
    """Used to lazy load a function's parameters as a partial.

    Handles the following request parameters:
        function: The id of the function object whose parameters should be rendered
        allow_template_variables: When true, the fields of the generated form will
            accept django template variables syntax (e.g. {{somevariable}}) in addition
            to data of the parameters natural type.
    """
    env = Environment.objects.get(id=request.session.get("environment_id"))

    if not request.user.has_perm(Permission.TASK_CREATE, env):
        return HttpResponseForbidden()

    if (tasked_id := request.GET.get("tasked_id")) in ["", None]:
        return HttpResponse("Nothing selected to task.")
    if (tasked_type := request.GET.get("tasked_type")) in ["", None]:
        return HttpResponse("Unable to determine task type")

    if request.GET.get("allow_template_variables") == "true":
        form_class = TaskParameterTemplateForm
    else:
        form_class = TaskParameterForm

    if tasked_type == "function":
        tasked_object = get_object_or_404(Function, id=tasked_id, environment=env)
    else:
        tasked_object = get_object_or_404(Workflow, id=tasked_id, environment=env)

    form = form_class(tasked_object=tasked_object, creator=request.user)
    return render(request, form.template_name, {"form": form})
