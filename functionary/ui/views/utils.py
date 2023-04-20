from django.http import HttpRequest

from core.auth import Permission
from core.models import Environment


def _set_session_permission(session, permission: str, user_has_permission: bool):
    """Set the value of the session permission variable"""
    model, action = permission.split(":")

    session[f"user_can_{action}_{model}"] = user_has_permission


def _load_session_permissions(request: HttpRequest, environment: Environment):
    """Load the user's permissions into the session for ease of access"""
    user_environment_permissions = request.user.environment_permissions(
        environment=environment, inherited=True
    )

    # Start with all permissions set to False to effectively zero out
    # any permissions granted from the previously selected environment
    for permission in Permission:
        _set_session_permission(request.session, permission.value, False)

    for permission in user_environment_permissions:
        _set_session_permission(request.session, permission, True)


def set_session_environment(request: HttpRequest, environment: Environment) -> None:
    """Set the environment for the session

    For any session there is always a single active environment. This function
    adds the environment to the session as "environment_id" and the user's permissions
    for that environment, with entries in the form of "user_can_<action>_<model>". For
    example:

        * user_can_create_task
        * user_can_update_workflow

    This makes it possible to do easy checks in a template, for example, by
    ensuring the request is in the context and then doing a simple check such as:

        {% if request.session.user_can_create_task %}

    The environment id will also be persisted in the user's "environment" preference
    so that it can be recalled during the login process and allow the user's next
    session to start in the environment they were last working.

    Args:
        request: The HttpRequest containing the session to update
        environment: The environment to make active for the session

    Returns:
        None
    """
    request.session["environment_id"] = str(environment.id)
    _load_session_permissions(request, environment)

    request.user.set_preference("environment", str(environment.id), save=True)
