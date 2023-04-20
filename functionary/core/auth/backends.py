import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend

from core.auth import Permission
from core.models import Environment, Team
from core.utils.constance import get_config
from core.utils.user import normalize_dn

logger = logging.getLogger(__name__)

UserModel = get_user_model()


class CoreBackend(BaseBackend):
    """Custom auth backend"""

    def authenticate(self, request, username=None, password=None, *args, **kwargs):
        """Authenticate using a Trusted Header if enabled and configured"""
        config = get_config(
            [
                "TRUSTED_HEADER_AUTHENTICATION_ENABLED",
                "TRUSTED_HEADER_AUTHENTICATION_HEADER",
                "TRUSTED_HEADER_AUTHENTICATION_USER_ATTRIBUTE",
            ]
        )

        if not (
            config.TRUSTED_HEADER_AUTHENTICATION_ENABLED
            and config.TRUSTED_HEADER_AUTHENTICATION_HEADER
        ):
            return None

        # To avoid confusion, do not authenticate if a username or password are
        # provided. Let the other authentication backends handle that.
        if username or password:
            return None

        if not (
            header_username := request.headers.get(
                config.TRUSTED_HEADER_AUTHENTICATION_HEADER
            )
        ):
            return None

        user_attribute = config.TRUSTED_HEADER_AUTHENTICATION_USER_ATTRIBUTE

        # Normalize the DN to the format that's used on the Admin page
        if user_attribute == "distinguished_name":
            try:
                header_username = normalize_dn(header_username)
            except ValueError:
                logging.warning("Unable to parse DN: %s", header_username)
                header_username = None

            # Abort if its empty so we don't erroneously match a user.
            if not header_username:
                return None
        lookup_params = {user_attribute: header_username}

        try:
            user = UserModel.objects.get(**lookup_params)
            return user if user.is_active else None
        except UserModel.DoesNotExist:
            return None

    def get_user(self, user_id):
        """Return the User object for the requested user_id"""
        try:
            return UserModel.objects.get(id=user_id)
        except UserModel.DoesNotExist:
            return None

    def _user_permissions_for_object(self, user, obj) -> set:
        """For a given Team or Environment, returns the user's assigned permissions."""
        if isinstance(obj, Team):
            return user.team_permissions(obj)
        elif isinstance(obj, Environment):
            return user.environment_permissions(obj, inherited=True)
        else:
            return set()

    def has_perm(self, user, perm, obj=None) -> bool:
        """Checks if a user has the supplied permission against a
        provided Team or Environment object.

        Args:
            user: User object
            perm: A string or Permission enum representing the permission to check
            obj: A Team or Environment object. Any other type will return False.

        Returns:
            Boolean representing whether the user has permission
        """

        if not isinstance(obj, (Environment, Team)):
            return False

        if not user.is_active:
            return False
        elif user.is_superuser:
            return True
        else:
            # Allow the perm to be either the enum or its value
            if isinstance(perm, Permission):
                perm = perm.value

            return perm in self._user_permissions_for_object(user, obj)
