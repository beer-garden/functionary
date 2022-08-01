from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import permissions
from rest_framework.exceptions import ParseError
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from builder.utils import extract_package_definition, initiate_build
from core.models import Environment

from ..serializers import BuildSerializer, PackageDefinitionSerializer


class PublishView(APIView):
    """View for submitting a package to be built and published."""

    # TODO: Authentication and permissions
    permission_classes = [permissions.IsAuthenticated]

    parser_classes = [MultiPartParser]

    # TODO: Add reference to package description YAML documentation once it exists
    @extend_schema(
        description=("Publish a package"),
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {
                    "package_contents": {
                        "type": "string",
                        "format": "binary",
                        "description": "gzipped tarball containing the package files",
                    },
                },
            }
        },
        responses={200: BuildSerializer},
        parameters=[
            OpenApiParameter(
                name="X-Team-Id", type=str, location=OpenApiParameter.HEADER
            ),
            OpenApiParameter(
                name="X-Environment-Id", type=str, location=OpenApiParameter.HEADER
            ),
        ],
    )
    def post(self, request, *args, **kwargs):
        """Receives the package contents and package definition files. The definition
        file is validated and then a new Build is created
        """
        # BinaryField is not supported by drf serializers, so we must validate the
        # request data ourselves
        self._validate_publish_input(request)

        package_contents_blob = request.FILES.get("package_contents").read()
        package_yaml = extract_package_definition(package_contents_blob)

        package_definition = package_yaml["package"]

        # If the package definition schema changes at any point, this would need to
        # identify the correct serializer based on the package_definition_version
        PackageDefinitionSerializer(data=package_definition).is_valid(
            raise_exception=True
        )

        # TODO: request.team and request.environment should be set automatically on
        #       every request via a mixin or similar solution
        environment_id = request.headers.get("X-Environment-Id")
        if environment_id is None:
            team_id = request.headers.get("X-Team-Id")
            request.environment = Environment.objects.get(
                team__id=team_id, default=True
            )
        else:
            request.environment = Environment.objects.get(id=environment_id)

        build = initiate_build(
            creator=request.user,
            environment=request.environment,
            package_contents=package_contents_blob,
            package_definition=package_definition,
            package_definition_version=package_yaml.get("version", "1.0"),
        )

        return Response(BuildSerializer(build).data)

    def _validate_publish_input(self, request):
        """Validates that the request includes all required data"""
        if request.FILES.get("package_contents") is None:
            raise ParseError(detail="package_contents is required and must be a file")
