""" Task serializers """
from collections import OrderedDict

from django.core.exceptions import ValidationError
from rest_framework import serializers

from core.api.v1.utils import cast_parameters, parse_parameters
from core.models import Function, Task, Workflow


class TaskSerializer(serializers.ModelSerializer):
    """Basic serializer for the Task model"""

    class Meta:
        model = Task
        fields = "__all__"


class TaskCreateBaseSerializerMixin:
    """Mixin for common components of Task creation serializers"""

    def to_internal_value(self, data) -> OrderedDict:
        parse_parameters(data)
        ret = super().to_internal_value(data)
        self.get_tasked_object(ret)
        cast_parameters(ret)
        return ret

    def create(self, validated_data):
        """Custom create that calls clean() on the task instance"""

        try:
            Task(**validated_data).clean()
        except ValidationError as exc:
            raise serializers.ValidationError(serializers.as_serializer_error(exc))

        return super().create(validated_data)


class TaskCreateByFunctionIdSerializer(
    TaskCreateBaseSerializerMixin, serializers.ModelSerializer
):
    """Serializer for creating a Task using the function id"""

    function = serializers.UUIDField()

    class Meta:
        model = Task
        fields = ["function", "parameters"]

    def get_tasked_object(self, values: OrderedDict) -> None:
        """Set the tasked_object from the provided function id"""
        function_id = values.pop("function")

        try:
            function: Function = Function.objects.get(id=function_id)
            values["tasked_object"] = function
        except Function.DoesNotExist:
            exception_map = {
                "function": (f"Could not find function with id {function_id}")
            }
            exc = ValidationError(exception_map)
            raise serializers.ValidationError(serializers.as_serializer_error(exc))


class TaskCreateByFunctionNameSerializer(
    TaskCreateBaseSerializerMixin, serializers.ModelSerializer
):
    """Serializer for creating a Task using the function and package name"""

    function_name = serializers.CharField()
    package_name = serializers.CharField()

    class Meta:
        model = Task
        fields = ["function_name", "package_name", "parameters"]

    def get_tasked_object(self, values: OrderedDict) -> None:
        """Set the tasked_object based on the supplied function_name and
        package_name
        """
        function_name = values.pop("function_name")
        package_name = values.pop("package_name")

        try:
            function = Function.objects.get(
                name=function_name,
                package__name=package_name,
            )
            values["tasked_object"] = function
        except Function.DoesNotExist:
            exception_map = {
                "function_name": (
                    f"No function {function_name} found for package {package_name}"
                )
            }
            exc = ValidationError(exception_map)
            raise serializers.ValidationError(serializers.as_serializer_error(exc))


class TaskCreateByWorkflowIdSerializer(
    TaskCreateBaseSerializerMixin, serializers.ModelSerializer
):
    """Serializer for creating a Task using the Workflow id"""

    workflow = serializers.UUIDField()

    class Meta:
        model = Task
        fields = ["workflow", "parameters"]

    def get_tasked_object(self, values: OrderedDict) -> None:
        """Set the tasked_object from the provided workflow id"""
        workflow_id = values.pop("workflow")

        try:
            workflow: Workflow = Workflow.objects.get(id=workflow_id)
            values["tasked_object"] = workflow
        except Workflow.DoesNotExist:
            exception_map = {
                "workflow": (f"Could not find workflow with id {workflow_id}")
            }
            exc = ValidationError(exception_map)
            raise serializers.ValidationError(serializers.as_serializer_error(exc))


class TaskCreateResponseSerializer(serializers.ModelSerializer):
    """Serializer for returning the task id after creation"""

    class Meta:
        model = Task
        fields = ["id"]


class TaskResultSerializer(serializers.ModelSerializer):
    """Basic serializer for the TaskResult model"""

    # SerializerMethodField is used because the actual data type of the result varies
    result = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = ["result"]

    def get_result(self, task: Task):
        return task.result
