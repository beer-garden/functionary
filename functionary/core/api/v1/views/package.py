from rest_framework import permissions

from core.api.viewsets import EnvironmentModelViewSet
from core.models import Package

from ..serializers import PackageSerializer


class PackageViewSet(EnvironmentModelViewSet):
    queryset = Package.objects.all()
    serializer_class = PackageSerializer
    permission_classes = [permissions.IsAuthenticated]
