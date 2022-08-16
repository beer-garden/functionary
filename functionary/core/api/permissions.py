from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission

from core.auth import Permission


class HasEnvironmentPermissionForAction(BasePermission):
    """Custom permission class that checks if the request user has the supplied
    permission for the request team or environment.

    This permission class should only be used in ViewSets that build off of
    EnvironmentViewMixin. It assumes the presence of verify_user_permission on the view.

    The permission checked is based off of the model of the view's queryset. If the view
    has no queryset, or an alternative model should be used, the name of the model
    can be supplied by settings the `permissioned_model` attribute on the ViewSet class.
    For example:

        permissioned_model = "Package"
    """

    method_action_map = {
        "POST": "CREATE",
        "GET": "READ",
        "OPTIONS": "READ",
        "HEAD": "READ",
        "PUT": "UPDATE",
        "PATCH": "UPDATE",
        "DELETE": "DELETE",
    }

    def _get_permission_for_request(self, request, view) -> str:
        """Construct the permission required for the request"""
        model_name = (
            getattr(view, "permissioned_model", None) or view.queryset.model.__name__
        ).upper()
        action = self.method_action_map.get(request.method)

        return getattr(Permission, f"{model_name}_{action}")

    def has_permission(self, request, view) -> bool:
        """Checks if the requesting user has the permission necessary to perform the
        requested action.

        Args:
            request: The django request object containing the user and request method
            view: A drf view class inheriting from EnvironmentViewMixin

        Returns:
            True if access should be granted. False otherwise.
        """
        permission = self._get_permission_for_request(request, view)

        try:
            view.verify_user_permission(permission)
        except PermissionDenied:
            # This should return False rather than raise as to allow for use in
            # conjunction with other permissions classes.
            return False

        return True
