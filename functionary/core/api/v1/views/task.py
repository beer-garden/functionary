from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import ValidationError as DjangoValidationError
from drf_spectacular.utils import (
    PolymorphicProxySerializer,
    extend_schema,
    extend_schema_view,
)
from rest_framework import mixins, serializers, status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.parsers import MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response

from core.api import HEADER_PARAMETERS
from core.api.permissions import HasEnvironmentPermissionForAction
from core.api.v1.serializers import (
    TaskCreateByFunctionIdSerializer,
    TaskCreateByFunctionNameSerializer,
    TaskCreateByWorkflowIdSerializer,
    TaskCreateResponseSerializer,
    TaskLogSerializer,
    TaskResultSerializer,
    TaskSerializer,
)
from core.api.v1.utils import PREFIX, SEPARATOR, get_parameter_name
from core.api.viewsets import EnvironmentGenericViewSet
from core.models import Task, TaskResult
from core.utils.minio import S3Error, handle_file_parameters
from core.utils.tasking import start_task

RENDER_PREFIX = f"{PREFIX}{SEPARATOR}".replace("\\", "")


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

    def get_serializer_class(self):
        if self.action == "create":
            input_keys = self.request.data.keys()
            if "function_name" in input_keys:
                return TaskCreateByFunctionNameSerializer
            elif "workflow" in input_keys:
                return TaskCreateByWorkflowIdSerializer
            else:
                return TaskCreateByFunctionIdSerializer
        else:
            return self.serializer_class

    @extend_schema(
        description=(
            "Execute a function. The function to be executed can be defined either "
            "by supplying function as a string uuid, or function_name and "
            "package_name. "
            "Parameters can be passed to the API either by prefixing them with "
            f"`{RENDER_PREFIX}`, or placing them inside a `parameters` JSON "
            "string. Prefixed parameters will **override** duplicate parameters "
            "inside the parameters JSON string."
        ),
        request=PolymorphicProxySerializer(
            component_name="TaskCreate",
            serializers={
                "function_by_id": TaskCreateByFunctionIdSerializer,
                "function_by_name": TaskCreateByFunctionNameSerializer,
                "workflow_by_id": TaskCreateByWorkflowIdSerializer,
            },
            resource_type_field_name=None,
        ),
        responses={
            status.HTTP_201_CREATED: TaskCreateResponseSerializer,
        },
        parameters=HEADER_PARAMETERS,
    )
    def create(self, request: Request, *args, **kwargs):
        data = request.data

        # Remove list elements that wrap singular values when multipart content
        data = request.data.dict()

        request_serializer: serializers.Serializer = self.get_serializer(data=data)
        request_serializer.is_valid(raise_exception=True)

        # TODO: Add API error handling when file upload fails.
        # Don't save file if upload fails.
        task = Task(
            creator=self.request.user,
            environment=self.get_environment(),
            **request_serializer.validated_data,
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
