""" Team serializers """
from rest_framework import serializers

from core.models import Team


class TeamSerializer(serializers.ModelSerializer):
    """Basic serializer for the Team model"""

    class Meta:
        model = Team
        fields = ["id", "name"]
