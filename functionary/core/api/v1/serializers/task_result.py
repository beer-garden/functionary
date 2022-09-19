""" TaskResult serializers """
from rest_framework import serializers

from core.models import TaskResult


class TaskResultSerializer(serializers.ModelSerializer):
    """Basic serializer for the TaskResult model"""

    class Meta:
        model = TaskResult
        fields = ["result"]
