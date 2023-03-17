""" Task serializers """
from collections import OrderedDict

from django.core.files.uploadedfile import InMemoryUploadedFile
from rest_framework import serializers

from core.api.v1.utils import PREFIX
from core.models import Function, Task, Workflow
from core.utils.parameter import PARAMETER_TYPE

field_types = {
    PARAMETER_TYPE.BOOLEAN: serializers.BooleanField,
    PARAMETER_TYPE.DATE: serializers.DateField,
    PARAMETER_TYPE.DATETIME: serializers.DateTimeField,
    PARAMETER_TYPE.FILE: serializers.FileField,
    PARAMETER_TYPE.FLOAT: serializers.FloatField,
    PARAMETER_TYPE.INTEGER: serializers.IntegerField,
    PARAMETER_TYPE.JSON: serializers.JSONField,
    PARAMETER_TYPE.STRING: serializers.CharField,
    PARAMETER_TYPE.TEXT: serializers.CharField,
}


class TaskSerializer(serializers.ModelSerializer):
    """Basic serializer for the Task model"""

    class Meta:
        model = Task
        fields = "__all__"


class TaskParameterSerializer(serializers.Serializer):
    """Serializer for handling task parameters"""

    def __init__(self, tasked_object: Function | Workflow, *args, **kwargs):
        """Custom init that takes a taskable object to determine parameter fields that
        should be added to the serializer.
        """
        super().__init__(*args, **kwargs)

        for parameter in tasked_object.parameters.all():
            field_class = field_types[parameter.parameter_type]
            self.fields[f"param.{parameter.name}"] = field_class(
                required=parameter.required
            )

    def _set_parameters(self, data: dict) -> None:
        """Renames param to parameters and converts and file parameter values to str"""
        if PREFIX not in data:
            return

        data["parameters"] = data.pop(PREFIX)

        for param in list(data["parameters"].keys()):
            value = data["parameters"][param]

            if type(value) == InMemoryUploadedFile:
                data["parameters"][param] = value.name

    def to_internal_value(self, data) -> OrderedDict:
        internal_value = super().to_internal_value(data)
        self._set_parameters(internal_value)
        return internal_value


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
