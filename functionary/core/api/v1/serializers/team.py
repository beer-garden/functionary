""" Team serializers """
from rest_framework import serializers

from core.models import Environment, Team


class TeamEnvironmentSerializer(serializers.ModelSerializer):
    """Serializer for listing a Team's environments"""

    class Meta:
        model = Environment
        fields = ["id", "name", "default"]


class TeamSerializer(serializers.ModelSerializer):
    """Basic serializer for the Team model"""

    environments = TeamEnvironmentSerializer(many=True)

    class Meta:
        model = Team
        fields = ["id", "name", "environments"]
