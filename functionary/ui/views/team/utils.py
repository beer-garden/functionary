from core.models import Team, TeamUserRole


def get_users(team: Team) -> list[dict]:
    """Get user data about all the users in the team

    Get a list of metadata about the users that are currently
    assigned to the given team.

    Args:
        team: The team to get the users from

    Returns:
        user_details: A list of dictionaries that contains information
            about the user and their relationship with the team
    """
    team_user_roles: list[TeamUserRole] = team.user_roles.all()

    user_details = []
    for team_user_role in team_user_roles:
        user_element = {}
        user_element["user"] = team_user_role.user
        user_element["role"] = team_user_role.role
        user_element["team_user_role_id"] = team_user_role.id
        user_details.append(user_element)
    return user_details
