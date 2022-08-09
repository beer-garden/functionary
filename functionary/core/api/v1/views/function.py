from rest_framework import permissions

from core.api.viewsets import EnvironmentReadOnlyModelViewSet
from core.models import Function

from ..serializers import FunctionSerializer


class FunctionViewSet(EnvironmentReadOnlyModelViewSet):
    queryset = Function.objects.all()
    serializer_class = FunctionSerializer
    permission_classes = [permissions.IsAuthenticated]
    environment_through_field = "package"
