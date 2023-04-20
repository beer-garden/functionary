from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import ValidationError as DjangoValidationError
from django_filters import rest_framework as filters
from drf_spectacular.utils import (
    PolymorphicProxySerializer,
    extend_schema,
    extend_schema_view,
)
from rest_framework import mixins, serializers, status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.parsers import JSONParser
from rest_framework.request import Request
from rest_framework.response import Response

from core.api import HEADER_PARAMETERS
from core.api.permissions import HasEnvironmentPermissionForAction
from core.api.v1.serializers import (
    TaskCreateByFunctionIdSchemaSerializer,
    TaskCreateByFunctionNameSchemaSerializer,
    TaskCreateByWorkflowIdSchemaSerializer,
    TaskCreateResponseSerializer,
    TaskLogSerializer,
    TaskParameterSerializer,
    TaskResultSerializer,
    TaskSerializer,
)
from core.api.viewsets import EnvironmentGenericViewSet
from core.models import Function, Task, TaskResult, Workflow
from core.utils.tasking import start_task

FUNCTION = "function"
WORKFLOW = "workflow"
FUNCTION_NAME = "function_name"
PACKAGE_NAME = "package_name"

TASK_CREATE_REQUEST_SCHEMA = PolymorphicProxySerializer(
    component_name="TaskCreate",
    serializers={
        "create_by_function_id": TaskCreateByFunctionIdSchemaSerializer,
        "create_by_function_name": TaskCreateByFunctionNameSchemaSerializer,
        "create_by_workflow_id": TaskCreateByWorkflowIdSchemaSerializer,
    },
    resource_type_field_name=None,
)

TASK_CREATE_REQUEST_DESCRIPTION = f"""
Execute a function or workflow. The id of the entity being tasked must be supplied via
either the `{FUNCTION}` or `{WORKFLOW}` parameter. Functions can alternatively be
tasked by name using `{FUNCTION_NAME}` and `{PACKAGE_NAME}`.
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

    queryset = (
        Task.objects.select_related("tasked_type")
        .prefetch_related("tasked_object")
        .all()
    )
    parser_classes = [JSONParser]
    serializer_class = TaskSerializer
    permission_classes = [HasEnvironmentPermissionForAction]

    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ("id", "status", "creator")

    def _get_tasked_object(self) -> Function | Workflow:
        """Parses the requests data to determined the object being tasked"""
        data = self.request.data
        input_keys = data.keys()
        environment = self.get_environment()

        try:
            if FUNCTION in input_keys:
                return Function.objects.get(id=data[FUNCTION], environment=environment)
            elif WORKFLOW in input_keys:
                return Workflow.objects.get(id=data[WORKFLOW], environment=environment)
            else:
                return Function.objects.get(
                    name=data.get(FUNCTION_NAME),
                    package__name=data.get(PACKAGE_NAME),
                    environment=environment,
                )
        except (ObjectDoesNotExist, DjangoValidationError):
            raise ValidationError("Invalid function or workflow provided")

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
        comment = data.get("comment")

        parameter_serializer = TaskParameterSerializer(
            tasked_object=tasked_object,
            data=data.get("parameters"),
            context={"request": request, "view": self},
        )
        _ = parameter_serializer.is_valid(raise_exception=True)

        task = Task(
            creator=self.request.user,
            environment=self.get_environment(),
            tasked_object=tasked_object,
            parameters=parameter_serializer.validated_data,
            comment=comment,
        )
        try:
            task.clean()
            task.save()
            start_task(task)
        except (ValidationError, DjangoValidationError) as err:
            raise serializers.ValidationError(serializers.as_serializer_error(err))

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
