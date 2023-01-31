from typing import Union

from core.auth import Role
from core.models import Environment, EnvironmentUserRole, Team, TeamUserRole, User


def get_user_role(
    user: User, environment: Environment
) -> tuple[
    Union[EnvironmentUserRole, TeamUserRole, None], Union[Environment, Team, None]
]:
    """Get the effective role of the user with respect to the Environment and Team

    This function returns the effective UserRole the user has within an environment,
    which is the highest role that user is currently assigned between the environment
    and the team. This function also returns a reference to the environment or team
    that their effective role is coming from.

    If the user is not part of the environment, and they are not on the team,
    returns a None for both return values.

    If the user has an EnvironmentUserRole, and their permissions are
    equivalent to their TeamUserRole, then the origin of their effective
    role will always be from the Environment.

    Args:
        user: User object for the user whose highest role you want to know
        environment: The target environment

    Returns:
        userrole, team|environment: Return a tuple with the UserRole object and the
            Environment or Team that role came from
        None, None: Return a tuple filled with None if user was not part of the
            team and environment
    """

    if user not in get_env_members(environment) and user not in get_team_members(
        environment
    ):
        return None, None

    if (
        env_user_role := EnvironmentUserRole.objects.filter(
            user=user, environment=environment
        ).first()
    ) is None:
        return (
            TeamUserRole.objects.get(user=user, team=environment.team),
            environment.team,
        )

    if (
        team_user_role := TeamUserRole.objects.filter(
            user=user, team=environment.team
        ).first()
    ) is None:
        return env_user_role, environment

    if Role[env_user_role.role] < Role[team_user_role.role]:
        return team_user_role, environment.team
    return env_user_role, environment


def get_users(env: Environment) -> list[dict]:
    """Get list of users who are part of the environment

    Get a list of users who have access to the environment. This includes
    the members of the team that the environment belongs to. The list will
    be sorted in decending order based on role.

    Args:
        env: The environment to get users from

    Returns:
        users: A list of dictionaries containing all the users who have
            access to the environment.
    """
    env_members = get_env_members(env)
    team_members = get_team_members(env)

    # Use set to remove duplicate users
    all_users = set(env_members + team_members)

    users = []
    for user in all_users:
        user_elements = {}
        role, origin = get_user_role(user, env)
        environment_user_role = EnvironmentUserRole.objects.filter(
            environment=env, user=user
        ).first()
        user_elements["user"] = user
        user_elements["role"] = role.role
        user_elements["origin"] = origin.name
        user_elements["environment_user_role_id"] = (
            environment_user_role.id if environment_user_role else None
        )
        users.append(user_elements)

    # Sort users by their username in ascending order
    users.sort(key=lambda x: x["user"].username)
    return users


def get_env_members(
    env: Environment,
) -> list[User]:
    """Get a list of all users in environment

    Return a list of all users in the environment

    Args:
        env: The environment to get the users from

    Returns:
        members: A list of all members of the environment
    """
    members: list[User] = [user.user for user in env.user_roles.all()]
    return members


def get_team_members(
    env: Environment,
) -> list[User]:
    """Get a list of all users in the env->team

    Return a list of all users on the team that owns the environment

    Args:
        env: The environment to get the users from

    Returns:
        members: A list of all members of the env->team
    """
    members: list[User] = [user.user for user in env.team.user_roles.all()]
    return members
