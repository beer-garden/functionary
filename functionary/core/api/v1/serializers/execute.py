""" Serializers for defining a package """
from rest_framework import serializers


class ExecuteSerializer(serializers.Serializer):
    """Serializer for the execute function endpoint"""

    package = serializers.CharField()
    function = serializers.CharField()
    parameters = serializers.JSONField()
