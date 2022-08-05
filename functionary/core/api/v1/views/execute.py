import logging

import jsonschema
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.api.mixins import EnvironmentViewMixin
from core.models.function import Function
from core.models.package import Package

from ...exceptions import BadRequest
from ..serializers.execute import ExecuteSerializer

logger = logging.getLogger(__name__)


class ExecuteView(APIView, EnvironmentViewMixin):
    """View for executing a function with specified parameters."""

    serializer_class = ExecuteSerializer
    # TODO: Proper permissions
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        description=("Execute a Function"),
        request=ExecuteSerializer,
        responses={200: None},  # Change to 201 when we have a response to send back
        parameters=EnvironmentViewMixin.header_parameters,
    )
    def post(self, request: Request) -> Response:
        """Accepts a package and function name and executes it with the passed
        parameters. The parameters are validated against the schema stored with the
        function prior to execution."""
        serializer = ExecuteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        package = serializer.validated_data["package"]
        function = serializer.validated_data["function"]

        logger.debug("Received request to call %s in %s", function, package)

        environment = self.get_environment()
        try:
            package_obj = Package.objects.get(
                environment_id=environment.id, name=package
            )
        except Package.DoesNotExist:
            raise BadRequest(f"Package not found: {package}")

        try:
            function_obj = Function.objects.get(package=package_obj.id, name=function)
        except Function.DoesNotExist:
            raise BadRequest(f"Function not found: {function}")

        try:
            jsonschema.validate(
                instance=serializer.validated_data["parameters"],
                schema=function_obj.schema,
            )
        except jsonschema.exceptions.ValidationError as ve:
            raise BadRequest(ve.message)

        stat = status.HTTP_200_OK  # Change to 201 when we have a response to send back

        # TODO Fire off tasking request

        return Response(status=stat)
