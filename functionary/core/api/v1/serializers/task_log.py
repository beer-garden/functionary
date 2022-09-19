""" TaskLog serializers """
from rest_framework import serializers

from core.models import TaskLog


class TaskLogSerializer(serializers.ModelSerializer):
    """Basic serializer for the TaskLog model"""

    class Meta:
        model = TaskLog
        fields = ["log"]
