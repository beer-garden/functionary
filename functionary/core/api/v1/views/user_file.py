from django.db.models import Q
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.status import HTTP_204_NO_CONTENT

from core.api import HEADER_PARAMETERS
from core.api.permissions import HasEnvironmentPermissionForAction
from core.api.v1.serializers import UserFileCreateSerializer, UserFileSerializer
from core.api.viewsets import EnvironmentGenericViewSet
from core.models import UserFile


@extend_schema_view(
    create=extend_schema(
        parameters=HEADER_PARAMETERS,
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {
                    "file": {"type": "string", "format": "binary"},
                    "public": {"type": "boolean"},
                },
            }
        },
    ),
    retrieve=extend_schema(parameters=HEADER_PARAMETERS),
    list=extend_schema(parameters=HEADER_PARAMETERS),
    destroy=extend_schema(parameters=HEADER_PARAMETERS),
)
class UserFileViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    EnvironmentGenericViewSet,
):
    """ViewSet for uploading, deleting, and listing UserFiles"""

    queryset = UserFile.objects.all()
    serializer_class = UserFileSerializer
    permission_classes = [HasEnvironmentPermissionForAction]

    def get_queryset(self):
        """Show public files in addition to the user's own files"""
        return (
            super().get_queryset().filter(Q(creator=self.request.user) | Q(public=True))
        )

    def create(self, request):
        context = self.get_serializer_context()
        serializer = UserFileCreateSerializer(data=request.data, context=context)

        if serializer.is_valid(raise_exception=True):
            serializer.save()

        response_serializer = UserFileSerializer(serializer.instance)

        return Response(response_serializer.data)

    def destroy(self, request, pk):
        """Custom destroy to check that the user owns the file they are attempting
        to delete
        """
        user_file = self.get_object()

        if self.request.user != user_file.creator:
            raise PermissionDenied

        user_file.delete()
        return Response(status=HTTP_204_NO_CONTENT)
