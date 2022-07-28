""" Function serializers """
from rest_framework import serializers

from core.models import Function


class FunctionSerializer(serializers.ModelSerializer):
    """Basic serializer for the Function model"""

    class Meta:
        model = Function
        fields = "__all__"
