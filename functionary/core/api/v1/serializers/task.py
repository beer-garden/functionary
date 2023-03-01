""" Task serializers """
from collections import OrderedDict

from django.core.exceptions import ValidationError
from rest_framework import serializers

from core.api.v1.utils import cast_parameters, parse_parameters
from core.models import Function, Task


class TaskSerializer(serializers.ModelSerializer):
    """Basic serializer for the Task model"""

    class Meta:
        model = Task
        fields = "__all__"


class TaskCreateByIdSerializer(serializers.ModelSerializer):
    """Serializer for creating a Task using the function id"""

    class Meta:
        model = Task
        fields = ["function", "parameters"]

    def to_internal_value(self, data) -> OrderedDict:
        parse_parameters(data)
        ret = super().to_internal_value(data)
        cast_parameters(ret)
        return ret

    def create(self, validated_data):
        """Custom create that calls clean() on the task instance"""

        try:
            Task(**validated_data).clean()
        except ValidationError as exc:
            raise serializers.ValidationError(serializers.as_serializer_error(exc))

        return super().create(validated_data)


class TaskCreateByNameSerializer(serializers.ModelSerializer):
    """Serializer for creating a Task using the function and package name"""

    function_name = serializers.CharField()
    package_name = serializers.CharField()

    class Meta:
        model = Task
        fields = ["function_name", "package_name", "parameters"]

    def to_internal_value(self, data: OrderedDict) -> OrderedDict:
        parse_parameters(data)
        ret = super().to_internal_value(data)
        self._get_function(ret)
        cast_parameters(ret)
        return ret

    def create(self, validated_data: OrderedDict):
        """Custom create that calls clean() on the task instance"""
        try:
            Task(**validated_data).clean()
        except ValidationError as exc:
            raise serializers.ValidationError(exc.message)

        return super().create(validated_data)

    def _get_function(self, values: OrderedDict) -> Function:
        """Substitute the function for the function_name and package_name

        Since this serializer does not substitute the Function before
        it's create method, we must fetch the function ourselves.

        Args:
            values: An ordered dict containing the values passed to the serializer

        Returns:
            function: The Function object

        Raises:
            ValidationError: If the function was not found
        """
        function_name = values.pop("function_name")
        package_name = values.pop("package_name")

        try:
            function: Function = Function.objects.get(
                name=function_name,
                package__name=package_name,
            )
            values["function"] = function
        except Function.DoesNotExist:
            exception_map = {
                "function_name": (
                    f"No function {function_name} found for package {package_name}"
                )
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
