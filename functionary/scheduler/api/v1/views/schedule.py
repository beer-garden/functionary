from rest_framework import permissions
from rest_framework.viewsets import ModelViewSet

from scheduler.models import Schedule

from ..serializers import ScheduleSerializer


class ScheduleViewSet(ModelViewSet):
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]
