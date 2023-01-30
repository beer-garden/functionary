from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseForbidden,
    HttpResponseRedirect,
    QueryDict,
)
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from core.auth import Permission
from core.models import Environment, Function, Task
from ui.forms.tasks import TaskParameterForm, TaskParameterTemplateForm

from .generic import PermissionedDetailView, PermissionedListView

PAGINATION_AMOUNT = 15


class FunctionListView(PermissionedListView):
    model = Function
    environment_through_field = "package"
    queryset = Function.objects.select_related("package").all()
    ordering = ["package__name", "name"]
    paginate_by = PAGINATION_AMOUNT


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
        env = function.package.environment
        form = None

        missing_variables = []
        if function.variables:
            all_vars = list(env.variables.values_list("name", flat=True))
            missing_variables = [
                var for var in function.variables if var not in all_vars
            ]
        context["missing_variables"] = missing_variables
        if self.request.user.has_perm(Permission.TASK_CREATE, env):
            form = TaskParameterForm(function)

        context["form"] = form.render("forms/task_parameters.html") if form else None
        return context


@require_POST
@login_required
def execute(request: HttpRequest) -> HttpResponse:
    func = None
    form = None

    env = Environment.objects.get(id=request.session.get("environment_id"))
    if not request.user.has_perm(Permission.TASK_CREATE, env):
        return HttpResponseForbidden()

    data: QueryDict = request.POST.copy()
    func = get_object_or_404(Function, id=data.get("function_id"))
    form = TaskParameterForm(func, data)

    if form.is_valid():

        # Clean the task fields before saving the Task
        try:
            # Create the new Task, the validated parameters are in form.cleaned_data
            task = Task(
                environment=env,
                creator=request.user,
                function=func,
                parameters=form.cleaned_data,
                return_type=func.return_type,
            )
            task.clean()
            task.save()

            # Redirect to the newly created task:
            return HttpResponseRedirect(reverse("ui:task-detail", args=(task.id,)))
        except ValidationError:
            form.add_error(
                None,
                ValidationError(
                    "The given parameters do not conform to function schema.",
                    code="invalid",
                ),
            )

    args = {"form": form, "function": func}
    return render(request, "core/function_detail.html", args)


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

    if (
        allow_template_variables := request.GET.get("allow_template_variables")
    ) and allow_template_variables.lower() == "true":
        form_class = TaskParameterTemplateForm
    else:
        form_class = TaskParameterForm

    if (function_id := request.GET.get("function")) in ["", None]:
        return HttpResponse("No function selected.")

    function = get_object_or_404(Function, id=function_id, environment=env)

    form = form_class(function=function)
    return render(request, form.template_name, {"form": form})
