from django_filters import rest_framework as filters

from builder.models import Build
from core.api.permissions import HasEnvironmentPermissionForAction
from core.api.viewsets import EnvironmentReadOnlyModelViewSet

from ..serializers import BuildSerializer


class BuildViewSet(EnvironmentReadOnlyModelViewSet):
    """View the status of package builds"""

    queryset = Build.objects.select_related("package", "creator").all()
    serializer_class = BuildSerializer
    permission_classes = [HasEnvironmentPermissionForAction]
    permissioned_model = "Package"
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ("id", "package__id", "package__name")
