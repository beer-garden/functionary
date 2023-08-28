from django_filters import rest_framework as filters

from core.api.permissions import HasEnvironmentPermissionForAction
from core.api.viewsets import EnvironmentModelViewSet
from core.models import Package

from ..serializers import PackageSerializer


class PackageViewSet(EnvironmentModelViewSet):
    """View for retrieving and updating packages"""

    queryset = Package.active_objects.all()
    serializer_class = PackageSerializer
    permission_classes = [HasEnvironmentPermissionForAction]
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ("id", "name", "display_name")
