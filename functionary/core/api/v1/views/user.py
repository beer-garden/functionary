from rest_framework import permissions
from rest_framework.viewsets import ReadOnlyModelViewSet

from core.models import User

from ..serializers import UserSerializer


class UserViewSet(ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
