from django.contrib.auth.backends import BaseBackend

from core.auth import Permission
from core.models import Environment, Team


class CoreBackend(BaseBackend):
    """Custom auth backend"""

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
