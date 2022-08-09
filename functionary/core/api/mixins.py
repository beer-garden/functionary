from functools import cache

from django.core.exceptions import ValidationError
from drf_spectacular.utils import OpenApiParameter

from core.models import Environment, Team

from .exceptions import BadRequest


class EnvironmentViewMixin:
    """Provides handling of the X-Environment-Id and X-Team-Id headers to determine
    the environment context of the request."""

    header_parameters = [
        OpenApiParameter(
            name="X-Team-Id",
            type=str,
            location=OpenApiParameter.HEADER,
            description=(
                "ID for the Team to which this request corresponds. If set, the "
                "default environment for the team will be used. This is ignored if "
                "X-Environment-Id is set."
            ),
        ),
        OpenApiParameter(
            name="X-Environment-Id",
            type=str,
            location=OpenApiParameter.HEADER,
            description=("ID for the Environment to which this request corresponds"),
        ),
    ]

    @cache
    def get_environment(self) -> Environment:
        """Retrieve the Environment object that corresponds to either the environment
        with id X-Environment-Id or the default environment for the team with id
        X-Team-Id.

        Returns:
            The appropriate Environment object based on the request headers

        Raises:
            InvalidHeader: The headers were missing or the environment could not be
                           determined based on the header values
        """
        environment_id = self.request.headers.get("X-Environment-Id")
        team_id = self.request.headers.get("X-Team-Id")

        if environment_id:
            try:
                environment_obj = Environment.objects.get(id=environment_id)
            except (Environment.DoesNotExist, ValidationError):
                raise BadRequest(f"No environment found with id {environment_id}")
        elif team_id:
            try:
                team_obj = Team.objects.get(id=team_id)
            except (Team.DoesNotExist, ValidationError):
                raise BadRequest(f"No team found with id {team_id}")

            try:
                environment_obj = team_obj.environments.get(default=True)
            except Environment.DoesNotExist:
                raise BadRequest(
                    f"No default environment for team {team_id}. "
                    "X-Environment-Id header is required."
                )
        else:
            raise BadRequest("X-Environment-Id or X-Team-Id header must be set")

        return environment_obj
