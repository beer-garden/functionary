from rest_framework import permissions
from rest_framework.viewsets import ModelViewSet

from core.models import Team

from ..serializers import TeamSerializer


class TeamViewSet(ModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    permission_classes = [permissions.IsAuthenticated]
