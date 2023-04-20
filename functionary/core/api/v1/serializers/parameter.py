""" Parameter serializers """
from rest_framework import serializers

from core.models import FunctionParameter


class FunctionParameterSerializer(serializers.ModelSerializer):
    type = serializers.CharField(source="parameter_type")

    class Meta:
        model = FunctionParameter
        fields = ["name", "description", "type", "default", "required"]
