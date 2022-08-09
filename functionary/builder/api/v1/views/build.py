from rest_framework import permissions

from builder.models import Build
from core.api.viewsets import EnvironmentReadOnlyModelViewSet

from ..serializers import BuildSerializer


class BuildViewSet(EnvironmentReadOnlyModelViewSet):
    queryset = Build.objects.all()
    serializer_class = BuildSerializer

    # TODO: Proper permissions
    permission_classes = [permissions.IsAuthenticated]
