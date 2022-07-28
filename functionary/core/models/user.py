from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models


class User(AbstractBaseUser, PermissionsMixin):
    """User model override.

    TODO Overhaul Django's base authentication/authorization. The standard Django
    permissions model is unlikely to map well to our use case. We're using
    PermissionMixin for now, but will eventually need to move away from it.

    Attributes:
        username: unique identifying string for the user.
        password: possibly temporary until a better authentication method exists.
        email: user email address.
        is_active: whether this user is considered active. Defaults to True.
        last_login: when this user last logged in to their account.
        created_at: when the user was first added to the system. Defaults to now.
    """

    username_validator = UnicodeUsernameValidator()

    username = models.CharField(
        max_length=64,
        db_index=True,
        unique=True,
        validators=[username_validator],
    )
    password = models.CharField(max_length=255)
    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=64)
    email = models.CharField(max_length=64, blank=True, default="")
    is_active = models.BooleanField(default=True)
    last_login = models.DateTimeField(blank=True, null=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    # TODO Possibly remove these fields after moving to our own permissions scheme
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = []
