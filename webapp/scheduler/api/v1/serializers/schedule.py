""" Schedule serializers """
from rest_framework.serializers import ModelSerializer
from scheduler.models import Schedule


class ScheduleSerializer(ModelSerializer):
    """Basic serializer for the Schedule model"""

    class Meta:
        model = Schedule
        fields = ["id", "name"]
