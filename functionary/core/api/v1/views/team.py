from rest_framework.viewsets import ReadOnlyModelViewSet

from core.models import Team

from ..serializers import TeamSerializer


class TeamViewSet(ReadOnlyModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
