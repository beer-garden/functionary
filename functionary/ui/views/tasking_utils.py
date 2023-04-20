import django_filters
from django.contrib.contenttypes.models import ContentType
from django.forms.widgets import Select
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy

from core.models import Environment, Function, Package, Workflow
from ui.views.filters import DisplayNameModelChoiceFilter


def _get_packages(request):
    """Filter packages to the session's environment"""
    return Package.active_objects.filter(
        environment__id=request.session.get("environment_id")
    )


class FunctionPackageFilter(django_filters.FilterSet):
    package = DisplayNameModelChoiceFilter(
        field_name="package",
        label="Package",
        queryset=_get_packages,
        widget=Select(
            attrs={
                "hx-get": reverse_lazy("ui:taskable-objects"),
                "hx-target": "#tasked_object",
                "hx-vals": '{"tasked_type": "function"}',
            }
        ),
    )

    class Meta:
        model = Function
        fields = ["package"]

    @property
    def qs(self):
        environment__id = self.request.session.get("environment_id")
        active_functions = Function.active_objects.filter(environment=environment__id)
        filter_functions = super().qs

        return active_functions & filter_functions


def get_package_filter(request) -> FunctionPackageFilter:
    """Helper method to create a default FunctionPackageFilter"""
    return FunctionPackageFilter(request=request)


def get_taskable_objects(request, tasked_type, filter=None):
    """Helper function that takes care of getting all the objects of tasked_type
    and filtering them to the environment. It also preserves any filters passed in.

    Args:
        request: the HttpRequest that triggered the call
        tasked_type: the type of the objects to be retrieved
        filter: optional filter to use for querying objects

    Returns:
        A tuple of the dictionary of objects grouped by Package or keyed as
        "workflows"
    """
    environment_id = request.session.get("environment_id")
    if tasked_type == "workflow":
        workflows = Workflow.active_objects.filter(environment__id=environment_id)
        objects = {"workflows": workflows} if workflows else {}
    else:
        objects = {}

        if filter:
            ungrouped = filter.qs.prefetch_related("package")
        else:
            ungrouped = Function.active_objects.filter(
                environment__id=environment_id
            ).prefetch_related("package")

        for obj in ungrouped:
            objects.setdefault(obj.package.display_name, []).append(obj)

    return objects


def add_data_values(data, environment_id, tasked_object, tasked_type):
    """Helper function to fill the data dict with the Environment,
    tasked_object and tasked_type."""
    data["environment"] = get_object_or_404(Environment, id=environment_id)
    data["tasked_object"] = tasked_object
    data["tasked_type"] = tasked_type


def get_tasked_object(data, environment_id):
    """Helper function to convert the id and type to a Function or Workflow.
    Returns the object as well as the type of the object.

    Args:
        data: dictionary containing the "tasked_id" and "tasked_type" of
           the object to retrieve.
        environment_id: the environment to filter the object to

    Returns:
        A tuple containing the tasked object and the ContentType object
        corresponding to the tasked_type

    Raises:
        ValueError if an unknown tasked_type is passed into data
    """
    tasked_id = data["tasked_id"]
    tasked_type = data["tasked_type"]
    tasked_obj = None

    if tasked_type == "function":
        tasked_obj = get_object_or_404(
            Function, id=tasked_id, environment_id=environment_id
        )
    elif tasked_type == "workflow":
        tasked_obj = get_object_or_404(
            Workflow, id=tasked_id, environment_id=environment_id
        )
    else:
        raise ValueError(f"Unknown type for task: {tasked_type}")

    tasked_type = ContentType.objects.get_for_model(tasked_obj)

    return (tasked_obj, tasked_type)
