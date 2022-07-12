""" Build serializers """
from rest_framework import serializers

from builder.models import Build


class BuildSerializer(serializers.ModelSerializer):
    """Basic serializer for the Build model"""

    class Meta:
        model = Build
        fields = "__all__"
