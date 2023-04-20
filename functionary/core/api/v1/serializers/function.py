""" Function serializers """
from rest_framework import serializers

from core.api.v1.serializers.parameter import FunctionParameterSerializer
from core.models import Function


class FunctionSerializer(serializers.ModelSerializer):
    """Basic serializer for the Function model"""

    parameters = FunctionParameterSerializer(many=True)

    class Meta:
        model = Function
        fields = "__all__"
