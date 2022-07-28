from rest_framework import permissions
from rest_framework.viewsets import ModelViewSet

from core.models import Function

from ..serializers import FunctionSerializer


class FunctionViewSet(ModelViewSet):
    queryset = Function.objects.all()
    serializer_class = FunctionSerializer
    permission_classes = [permissions.IsAuthenticated]
