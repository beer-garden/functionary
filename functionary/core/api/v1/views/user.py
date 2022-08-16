from rest_framework.viewsets import ReadOnlyModelViewSet

from core.models import User

from ..serializers import UserSerializer


class UserViewSet(ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
