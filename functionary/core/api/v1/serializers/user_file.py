""" UserFile serializers """
from rest_framework import serializers

from core.models import UserFile


class EnvironmentDefault:
    """Returns the environment for the request"""

    requires_context = True

    def __call__(self, serializer_field):
        return serializer_field.context["view"].get_environment()


class NameDefault:
    """Returns the name from the uploaded file if present"""

    requires_context = True

    def __call__(self, serializer_field):
        if file_ := serializer_field.context["request"].FILES.get("file"):
            return file_.name
        else:
            return None


class UserFileSerializer(serializers.ModelSerializer):
    """Basic serializer for the UserFile model"""

    creator = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = UserFile
        fields = "__all__"


class UserFileCreateSerializer(serializers.ModelSerializer):
    """Serializer for UserFile create"""

    environment = serializers.HiddenField(default=EnvironmentDefault())
    name = serializers.HiddenField(default=NameDefault())
    creator = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = UserFile
        fields = ["file", "public", "environment", "name", "creator"]
