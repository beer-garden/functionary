import logging

import jsonschema
from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models.function import Function
from core.models.package import Package
from core.models.team import Team

from ..serializers.execute import ExecuteSerializer

logger = logging.getLogger(__name__)


class ExecuteView(APIView):
    serializer_class = ExecuteSerializer
    # TODO: Proper permissions
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request) -> Response:
        serial = ExecuteSerializer(data=request.data)
        serial.is_valid(raise_exception=True)
        package = serial.validated_data["package"]
        function = serial.validated_data["function"]

        logger.info("Received request to call %s in %s", function, package)

        team = Team.objects.get(name="users")
        # dir(team)
        try:
            env_id = "036d0e9d-bbc3-4277-9f8a-28a3861564aa"
            pack = Package.objects.get(environment_id=env_id, name=package)
            # pack = Package.objects.get(environment_id=team.id, name=package)
        except Package.DoesNotExist:
            stat = status.HTTP_400_BAD_REQUEST
            data = {"message": "Package not found"}
            return Response(data, stat)

        logger.debug("Looking for %s", function)
        try:
            func = Function.objects.get(package=pack.id, name=function)
        except Function.DoesNotExist:
            stat = status.HTTP_400_BAD_REQUEST
            data = {"message": "Function not found"}
            return Response(data, stat)

        try:
            jsonschema.validate(
                instance=serial.validated_data["parameters"], schema=func.schema
            )
        except jsonschema.exceptions.ValidationError as ve:
            stat = status.HTTP_400_BAD_REQUEST
            data = {"message": ve.message}
            return Response(data, stat)

        logger.info(f"Validation passed, executing {func.name}")

        stat = status.HTTP_200_OK

        # TODO Fire off tasking request

        return Response(status=stat)
