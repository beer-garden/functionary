from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import ValidationError as DjangoValidationError
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, serializers, status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.parsers import MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response

from core.api import HEADER_PARAMETERS
from core.api.permissions import HasEnvironmentPermissionForAction
from core.api.v1.serializers import (
    TaskCreateResponseSerializer,
    TaskLogSerializer,
    TaskParameterSerializer,
    TaskResultSerializer,
    TaskSerializer,
)
from core.api.v1.utils import PREFIX, SEPARATOR, get_parameter_name
from core.api.viewsets import EnvironmentGenericViewSet
from core.models import Function, Task, TaskResult, Workflow
from core.utils.minio import S3Error, handle_file_parameters
from core.utils.tasking import start_task

RENDER_PREFIX = f"{PREFIX}{SEPARATOR}".replace("\\", "")
FUNCTION = "function"
WORKFLOW = "workflow"
FUNCTION_NAME = "function_name"
PACKAGE_NAME = "package_name"

# Getting drf-spectacular to handle "additionalProperties" for serializers proved
# troublesome, so we construct the schema manually for now.
TASK_CREATE_REQUEST_SCHEMA = {
    "multipart/form-data": {
        "oneOf": [
            {
                "type": "object",
                "additionalProperties": True,
                "properties": {
                    FUNCTION: {
                        "type": "string",
                        "format": "uuid",
                        "description": "Function id",
                    },
                },
                "required": [FUNCTION],
            },
            {
                "type": "object",
                "additionalProperties": True,
                "properties": {
                    FUNCTION_NAME: {
                        "type": "string",
                        "description": ("Function name"),
                    },
                    PACKAGE_NAME: {
                        "type": "string",
                        "description": ("Package name"),
                    },
                },
                "required": [FUNCTION_NAME, PACKAGE_NAME],
            },
            {
                "type": "object",
                "additionalProperties": True,
                "properties": {
                    WORKFLOW: {
                        "type": "string",
                        "format": "uuid",
                        "description": "Workflow id",
                    },
                },
                "required": [WORKFLOW],
            },
        ]
    }
}

TASK_CREATE_REQUEST_DESCRIPTION = f"""
Execute a function or workflow. The id of the entity being tasked must be supplied via
either the `{FUNCTION}` or `{WORKFLOW}` parameter. Functions can alternatively be
tasked by name using `{FUNCTION_NAME}` and `{PACKAGE_NAME}`. Parameters to be passed to
the function or workflow are supplied by prefixing the parameter name with
`{RENDER_PREFIX}`. For example `{RENDER_PREFIX}input`, `{RENDER_PREFIX}duration`, etc.
"""


@extend_schema_view(
    retrieve=extend_schema(parameters=HEADER_PARAMETERS),
    list=extend_schema(parameters=HEADER_PARAMETERS),
)
class TaskViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    EnvironmentGenericViewSet,
):
    """View for creating and retrieving tasks"""

    queryset = Task.objects.all()
    parser_classes = [MultiPartParser]
    serializer_class = TaskSerializer
    permission_classes = [HasEnvironmentPermissionForAction]

    def _get_tasked_object(self) -> Function | Workflow:
        """Parses the requests data to determined the object being tasked"""
        data = self.request.POST
        input_keys = data.keys()

        try:
            if FUNCTION in input_keys:
                return Function.objects.get(id=data[FUNCTION])
            elif WORKFLOW in input_keys:
                return Workflow.objects.get(id=data[WORKFLOW])
            else:
                return Function.objects.get(
                    name=data.get(FUNCTION_NAME),
                    package__name=data.get(PACKAGE_NAME),
                )
        except (ObjectDoesNotExist, DjangoValidationError):
            raise ValidationError("Invalid function or workflow provided")

    def _handle_extra_parameters(self, serializer: TaskParameterSerializer) -> None:
        """Raises ValidationError if the request data includes unexpected input. This
        is to ensure mistyped optional parameters are not silently ignored.
        """
        task_parameter_fields = list(serializer.fields.keys())
        tasked_object_fields = [
            FUNCTION,
            WORKFLOW,
            FUNCTION_NAME,
            PACKAGE_NAME,
        ]

        valid_input = task_parameter_fields + tasked_object_fields

        invalid_parameters = [
            parameter
            for parameter in self.request.POST.keys()
            if parameter not in valid_input
        ]

        if len(invalid_parameters) > 0:
            raise ValidationError(
                f"Invalid parameters provided: {invalid_parameters}. "
                f"Remember to use the '{RENDER_PREFIX}' prefix for tasking parameters."
            )

    @extend_schema(
        description=TASK_CREATE_REQUEST_DESCRIPTION,
        request=TASK_CREATE_REQUEST_SCHEMA,
        responses={
            status.HTTP_201_CREATED: TaskCreateResponseSerializer,
        },
        parameters=HEADER_PARAMETERS,
    )
    def create(self, request: Request, *args, **kwargs):
        data = request.data
        tasked_object = self._get_tasked_object()

        task_parameter_serializer = TaskParameterSerializer(
            tasked_object=tasked_object, data=data
        )
        task_parameter_serializer.is_valid(raise_exception=True)
        self._handle_extra_parameters(task_parameter_serializer)

        # TODO: Add API error handling when file upload fails.
        # Don't save file if upload fails.
        task = Task(
            creator=self.request.user,
            environment=self.get_environment(),
            tasked_object=tasked_object,
            **task_parameter_serializer.validated_data,
        )
        try:
            task.clean()
            _handle_file_parameters(request, task)
            task.save()
            start_task(task)
        except (ValidationError, DjangoValidationError) as err:
            raise serializers.ValidationError(serializers.as_serializer_error(err))
        except S3Error as err:
            return Response(
                {"error": f"{err}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        response_serializer = TaskCreateResponseSerializer(task)

        headers = self.get_success_headers(response_serializer.data)

        return Response(
            response_serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    @extend_schema(
        description="Retrieve the task results",
        parameters=HEADER_PARAMETERS,
        responses={status.HTTP_200_OK: TaskResultSerializer},
    )
    @action(methods=["get"], detail=True)
    def result(self, request, pk=None):
        task = self.get_object()

        if not TaskResult.objects.filter(task=task).exists():
            raise NotFound(f"No result found for task {pk}.")

        serializer = TaskResultSerializer(task)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        description="Retrieve the task log output",
        parameters=HEADER_PARAMETERS,
        responses={status.HTTP_200_OK: TaskLogSerializer},
    )
    @action(methods=["get"], detail=True)
    def log(self, request, pk=None):
        task = self.get_object()

        try:
            serializer = TaskLogSerializer(task.tasklog)
        except ObjectDoesNotExist:
            raise NotFound(f"No log found for task {pk}.")

        return Response(serializer.data, status=status.HTTP_200_OK)


def _handle_file_parameters(
    request: Request,
    task: Task,
) -> None:
    """Mutate the file parameter names passed to the API

    Arguments:
        request: The originating API request
        task: The Task object created as a result of the request

    Returns:
        None
    """
    if not request.FILES:
        return

    # Wrap items in list to avoid dictionary changed size error
    for param, _ in list(request.FILES.items()):
        if param_name := get_parameter_name(param):
            request.FILES[param_name] = request.FILES.pop(param)[0]

    handle_file_parameters(task, request)
