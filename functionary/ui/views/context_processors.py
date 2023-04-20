from django.http import HttpRequest

from core.utils.constance import get_config


def user_environments(request: HttpRequest) -> dict:
    """Adds the user's environments to the context

    Args:
        request: The HttpRequest to base the context on

    Returns:
        A dict containing "user_environments" to be appended to the template context
    """
    environments = {}

    if hasattr(request.user, "environments"):
        envs = request.user.environments.select_related("team").order_by(
            "team__name", "name"
        )

        for env in envs:
            environments.setdefault(env.team.name, []).append(env)

    return {"user_environments": environments}


def active_nav(request: HttpRequest) -> dict:
    """Determines which nav item on the navbar should be active

    Args:
        request: The HttpRequest to base the context on

    Returns:
        A dict containing "active_nav" to be appended to the template context
    """
    nav_item = request.resolver_match.url_name.split("-")[0]

    return {"active_nav": nav_item}


def settings(request: HttpRequest) -> dict:
    """Adds values from the settings object to the context

    Args:
        request: The HttpRequest to base the context on

    Returns:
        A dict containing "settings" to be appended to the template context
    """
    config = get_config(
        [
            "UI_BANNER_1_BG",
            "UI_BANNER_1_FG",
            "UI_BANNER_1_TEXT",
            "UI_BANNER_2_BG",
            "UI_BANNER_2_FG",
            "UI_BANNER_2_TEXT",
        ]
    )
    # Use getattr() or to override a blank value for color
    banner_1 = {
        "text": config.UI_BANNER_1_TEXT,
        "bg": getattr(config, "UI_BANNER_1_BG") or "var(--bs-primary-bg-subtle)",
        "fg": getattr(config, "UI_BANNER_1_FG") or "var(--bs-primary)",
    }
    banner_2 = {
        "text": config.UI_BANNER_2_TEXT,
        "bg": getattr(config, "UI_BANNER_2_BG") or "var(--bs-primary-bg-subtle)",
        "fg": getattr(config, "UI_BANNER_2_FG") or "var(--bs-primary)",
    }
    banner_config = [banner_1] if all(banner_1.values()) else []
    if all(banner_2.values()):
        banner_config.append(banner_2)

    # The correct bootstrap class is pb/t-4 for one line and -5 for two
    banner_pad = 3 + len(banner_config) if banner_config else 0

    return {"settings": {"banners": banner_config, "banner_pad": banner_pad}}
