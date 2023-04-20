from django_filters.views import FilterView

from core.auth import Operation
from core.models import Function
from ui.views.generic import PermissionedViewMixin
from ui.views.tasking_utils import FunctionPackageFilter, get_taskable_objects


class TaskableObjectsView(PermissionedViewMixin, FilterView):
    """View that reloads the selectable Functions and Workflows"""

    model = Function
    filterset_class = FunctionPackageFilter
    permissioned_model = "Function"
    post_action = Operation.READ
    template_name = "partials/tasked_object_chooser.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        tasked_type = self.request.GET.get("tasked_type", "function")
        objects = get_taskable_objects(
            self.request,
            tasked_type,
            filter=context["filter"],
        )

        context["taskable_objects"] = objects
        context["tasked_type"] = tasked_type
        context["clear_parameters"] = True

        return context
