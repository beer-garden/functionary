from rest_framework import permissions
from rest_framework.viewsets import ModelViewSet

from core.models import Package

from ..serializers import PackageSerializer


class PackageViewSet(ModelViewSet):
    queryset = Package.objects.all()
    serializer_class = PackageSerializer
    permission_classes = [permissions.IsAuthenticated]
