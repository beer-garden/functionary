from unittest.mock import Mock

import pytest

from core.auth.backends import CoreBackend
from core.models import User

TRUSTED_HEADER = "X-Username"


@pytest.fixture
def user():
    user_ = User.objects.create(
        username="testuser", distinguished_name="CN=Test User,OU=Organization,C=US"
    )
    user_.set_password("password")

    return user_


@pytest.mark.django_db
@pytest.mark.override_config(
    TRUSTED_HEADER_AUTHENTICATION_HEADER=TRUSTED_HEADER,
    TRUSTED_HEADER_AUTHENTICATION_ENABLED=True,
)
def test_core_backend_can_authenticate_via_username_trusted_header(user):
    """CoreBackend should authenticate a user by username via a trusted header"""
    request = Mock()
    request.headers = {TRUSTED_HEADER: user.username}

    assert CoreBackend().authenticate(request) == user


@pytest.mark.django_db
@pytest.mark.override_config(
    TRUSTED_HEADER_AUTHENTICATION_HEADER=TRUSTED_HEADER,
    TRUSTED_HEADER_AUTHENTICATION_ENABLED=True,
    TRUSTED_HEADER_AUTHENTICATION_USER_ATTRIBUTE="distinguished_name",
)
def test_core_backend_can_authenticate_via_dn_trusted_header(user: User):
    """CoreBackend should authenticate a user by dn via a trusted header"""
    request = Mock()
    request.headers = {TRUSTED_HEADER: user.distinguished_name}

    assert CoreBackend().authenticate(request) == user

    # Verify the ", " doesn't effect matching the DN
    distinguished_name = user.distinguished_name.replace(",", ", ")
    request.headers = {TRUSTED_HEADER: distinguished_name}

    assert CoreBackend().authenticate(request) == user

    # Verify that lowercasing the RDN key doesn't effect matching
    distinguished_name = distinguished_name[0:2].lower() + distinguished_name[2:]
    request.headers = {TRUSTED_HEADER: distinguished_name}

    assert CoreBackend().authenticate(request) == user


@pytest.mark.django_db
@pytest.mark.override_config(
    TRUSTED_HEADER_AUTHENTICATION_HEADER=TRUSTED_HEADER,
    TRUSTED_HEADER_AUTHENTICATION_ENABLED=True,
    TRUSTED_HEADER_AUTHENTICATION_USER_ATTRIBUTE="distinguished_name",
)
def test_core_backend_distinguished_name_values_case_sensitive(user: User):
    """CoreBackend should reject a distinguished name that only differs in case"""
    dn = user.distinguished_name[:-2] + user.distinguished_name[-2:].lower()
    request = Mock()
    request.headers = {TRUSTED_HEADER: dn}

    assert CoreBackend().authenticate(request) is None


@pytest.mark.django_db
@pytest.mark.override_config(
    TRUSTED_HEADER_AUTHENTICATION_HEADER=None,
    TRUSTED_HEADER_AUTHENTICATION_ENABLED=True,
)
def test_core_backend_authenticate_handles_nonexistent_user(user: User):
    """CoreBackend.authenticate should return None if the provided user does not
    exist"""
    request = Mock()
    request.headers = {TRUSTED_HEADER: "notauser"}

    assert CoreBackend().authenticate(request) is None


@pytest.mark.django_db
@pytest.mark.override_config(
    TRUSTED_HEADER_AUTHENTICATION_HEADER=TRUSTED_HEADER,
    TRUSTED_HEADER_AUTHENTICATION_ENABLED=False,
)
def test_core_backend_rejects_if_trusted_header_disabled(user: User):
    """CoreBackend should not authenticate a user via a trusted header if trusted header
    auth is not enabled."""
    request = Mock()
    request.headers = {TRUSTED_HEADER: user.username}

    assert CoreBackend().authenticate(request) is None


@pytest.mark.django_db
@pytest.mark.override_config(
    TRUSTED_HEADER_AUTHENTICATION_HEADER=None,
    TRUSTED_HEADER_AUTHENTICATION_ENABLED=True,
)
def test_core_backend_rejects_if_trusted_header_not_configured(
    user: User,
):
    """CoreBackend should not authenticate a user via a trusted header if trusted header
    auth is not configured, even if it is enabled."""
    request = Mock()
    request.headers = {TRUSTED_HEADER: user.username}

    assert CoreBackend().authenticate(request) is None


@pytest.mark.django_db
@pytest.mark.override_config(
    TRUSTED_HEADER_AUTHENTICATION_HEADER=TRUSTED_HEADER,
    TRUSTED_HEADER_AUTHENTICATION_ENABLED=True,
)
def test_core_backend_rejects_with_username_and_password(user: User):
    """CoreBackend should not authenticate if a username and password are supplied,
    even if the header value is valid."""
    request = Mock()
    request.headers = {TRUSTED_HEADER: user.username}

    assert CoreBackend().authenticate(request, password="failme") is None
    assert CoreBackend().authenticate(request, username="failme") is None
    assert (
        CoreBackend().authenticate(request, username=user.username, password="password")
        is None
    )


@pytest.mark.django_db
@pytest.mark.override_config(
    TRUSTED_HEADER_AUTHENTICATION_HEADER=TRUSTED_HEADER,
    TRUSTED_HEADER_AUTHENTICATION_ENABLED=True,
)
def test_core_backend_rejects_inactive_user(user: User):
    """CoreBackend should not authenticate inactive users"""
    request = Mock()
    request.headers = {TRUSTED_HEADER: user.username}
    user.is_active = False
    user.save()

    assert CoreBackend().authenticate(request) is None


@pytest.mark.django_db
@pytest.mark.override_config(
    TRUSTED_HEADER_AUTHENTICATION_HEADER=TRUSTED_HEADER,
    TRUSTED_HEADER_AUTHENTICATION_ENABLED=True,
    TRUSTED_HEADER_AUTHENTICATION_USER_ATTRIBUTE="distinguished_name",
)
def test_core_backend_rejects_no_header_present_with_dn_trusted_header(user: User):
    """CoreBackend should not authenticate if no header is presented when using
    distinguished_name as the user attrtibute, even if a user with no dn exists."""
    request = Mock()
    request.headers = {}
    user.distinguished_name = None
    user.save()

    assert CoreBackend().authenticate(request) is None

    # An empty distinguished_name field should also not authenticate
    request.headers = {TRUSTED_HEADER: ""}
    user.distinguished_name = ""
    user.save()

    assert CoreBackend().authenticate(request) is None

    # Multiple users existing with no dn should still be handled gracefully.
    User.objects.create(username="anotheruser")
    assert CoreBackend().authenticate(request) is None
