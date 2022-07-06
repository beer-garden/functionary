from rest_framework import permissions
from rest_framework.viewsets import ModelViewSet

from core.models import User

from ..serializers import UserSerializer


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
