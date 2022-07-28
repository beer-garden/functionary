from rest_framework import permissions
from rest_framework.viewsets import ModelViewSet

from builder.models import Build

from ..serializers import BuildSerializer


class BuildViewSet(ModelViewSet):
    queryset = Build.objects.all()
    serializer_class = BuildSerializer

    # TODO: Proper permissions
    permission_classes = [permissions.IsAuthenticated]
