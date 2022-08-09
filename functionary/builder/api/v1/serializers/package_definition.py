""" Serializers for defining a package """
from rest_framework import serializers


class ParameterOptionSerializer(serializers.Serializer):
    name = serializers.CharField()

    # TODO: This should probably preserve numeric values rather than convert
    #       them to a string
    value = serializers.CharField()


class ParameterSerializer(serializers.Serializer):
    """Serializer for parameter description"""

    name = serializers.CharField()
    display_name = serializers.CharField(required=False)
    description = serializers.CharField(required=False)

    # TODO: This should likely be limited to known choices
    type = serializers.CharField(required=True)

    required = serializers.BooleanField(default=False)
    options = ParameterOptionSerializer(many=True, required=False)

    # TODO: This should probably preserve numeric values rather than convert
    #       them to a string
    default = serializers.CharField(required=False)


class FunctionSerializer(serializers.Serializer):
    """Serializer for function description"""

    name = serializers.CharField()
    display_name = serializers.CharField(required=False)
    description = serializers.CharField(required=False)
    parameters = ParameterSerializer(many=True)


class PackageDefinitionSerializer(serializers.Serializer):
    """Serializer for package description"""

    name = serializers.CharField()
    display_name = serializers.CharField(required=False)
    description = serializers.CharField(required=False)
    language = serializers.CharField(required=False)
    filename = serializers.CharField(required=False)
    environment = serializers.DictField(child=serializers.CharField(), required=False)
    functions = FunctionSerializer(many=True)


class PackageDefinitionWithVersionSerializer(serializers.Serializer):
    """Serializer for full package.yaml"""

    version = serializers.CharField()
    package = PackageDefinitionSerializer()
