""" Task serializers """
from django.db.models import Q
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from core.models import Function, Task, UserFile, Workflow
from core.utils.parameter import PARAMETER_TYPE


class FileRelatedField(serializers.PrimaryKeyRelatedField):
    """Field that can verify that the supplied UUID corresponds to a UserFile that the
    requesting user is allowed to use."""

    queryset = UserFile.objects.all()

    def get_queryset(self):
        """If a request context is provided, limit the queryset to UserFiles that the
        requesting user is allowed to access."""
        if not self.context:
            return self.queryset

        request = self.context.get("request")
        view = self.context.get("view")

        if not (request and view):
            raise ValueError("Expected 'request' and 'view' in context")

        return self.queryset.filter(environment=view.get_environment()).filter(
            Q(creator=request.user) | Q(public=True)
        )

    def to_internal_value(self, data):
        """Ensure the data is a properly formatted UUID and cast as str for use in
        JSON."""
        super().to_internal_value(data)

        return str(data)


field_types = {
    PARAMETER_TYPE.BOOLEAN: serializers.BooleanField,
    PARAMETER_TYPE.DATE: serializers.DateField,
    PARAMETER_TYPE.DATETIME: serializers.DateTimeField,
    PARAMETER_TYPE.FILE: FileRelatedField,
    PARAMETER_TYPE.FLOAT: serializers.FloatField,
    PARAMETER_TYPE.INTEGER: serializers.IntegerField,
    PARAMETER_TYPE.JSON: serializers.JSONField,
    PARAMETER_TYPE.STRING: serializers.CharField,
    PARAMETER_TYPE.TEXT: serializers.CharField,
}


class TaskSerializer(serializers.ModelSerializer):
    """Basic serializer for the Task model"""

    tasked_object_type = serializers.SerializerMethodField(source="tasked_type")
    tasked_object = serializers.SerializerMethodField(source="tasked_object")

    class Meta:
        model = Task
        fields = [
            "id",
            "tasked_object_type",
            "tasked_object",
            "parameters",
            "return_type",
            "status",
            "created_at",
            "updated_at",
            "environment",
            "creator",
            "scheduled_task",
            "comment",
        ]

    def get_tasked_object_type(self, instance) -> str:
        return instance.tasked_type.model

    def get_tasked_object(self, instance):
        tasked_obj = {"id": instance.tasked_id, "name": instance.tasked_object.name}
        if isinstance(instance.tasked_object, Function):
            tasked_obj.update({"package_name": instance.tasked_object.package.name})
        return tasked_obj


class TaskParameterSerializer(serializers.Serializer):
    """Serializer for handling task parameters"""

    def __init__(self, tasked_object: Function | Workflow, *args, **kwargs):
        """Custom init that takes a taskable object to determine parameter fields that
        should be added to the serializer.
        """
        super().__init__(*args, **kwargs)

        for parameter in tasked_object.parameters.all():
            field_kwargs = {}
            if parameter.options:
                field_class = serializers.ChoiceField
                field_kwargs = {"choices": parameter.options}
            else:
                field_class = field_types[parameter.parameter_type]
            self.fields[parameter.name] = field_class(
                required=parameter.required, **field_kwargs
            )

    def _check_for_unexpected_parameters(self):
        """Ensure that no unexpected parameters are present. This is to avoid
        silently ignoring typos or mistakes in parameter names."""
        allowed_fields = set(self.fields.keys())
        input_fields = set(self.initial_data.keys())

        additional_fields = input_fields - allowed_fields

        if len(additional_fields) > 0:
            self._errors["fields"] = [
                f"Unexpected parameters: {list(additional_fields)}"
            ]

    def is_valid(self, raise_exception=False):
        super().is_valid(raise_exception=False)
        self._check_for_unexpected_parameters()

        if self._errors and raise_exception:
            raise ValidationError(self.errors)


class TaskCreateResponseSerializer(serializers.ModelSerializer):
    """Serializer for returning the task id after creation"""

    class Meta:
        model = Task
        fields = ["id"]


class TaskCreateByFunctionIdSchemaSerializer(serializers.Serializer):
    """Serializer defining the schema for creating tasks using the Function id.
    Not intended for actual serialization."""

    function = serializers.UUIDField()
    parameters = serializers.JSONField()
    comment = serializers.CharField()


class TaskCreateByFunctionNameSchemaSerializer(serializers.Serializer):
    """Serializer defining the schema for creating tasks using the Function name.
    Not intended for actual serialization."""

    function_name = serializers.CharField()
    package_name = serializers.CharField()
    parameters = serializers.JSONField()
    comment = serializers.CharField()


class TaskCreateByWorkflowIdSchemaSerializer(serializers.Serializer):
    """Serializer defining the schema for creating tasks using the Workflow id.
    Not intended for actual serialization."""

    workflow = serializers.UUIDField()
    parameters = serializers.JSONField()
    comment = serializers.CharField()


class TaskResultSerializer(serializers.ModelSerializer):
    """Basic serializer for the TaskResult model"""

    # SerializerMethodField is used because the actual data type of the result varies
    result = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = ["result"]

    def get_result(self, task: Task) -> bool | dict | float | int | list | str | None:
        return task.result
