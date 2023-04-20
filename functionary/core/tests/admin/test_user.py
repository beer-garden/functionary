import pytest

from core.admin.user import UserAdminChangeForm
from core.models import User


@pytest.fixture
def user():
    return User.objects.create(username="user")


@pytest.mark.django_db
def test_change_user_normalizes_dn(user):
    """Test that the normalize_dn function is run on form clean."""
    dn = "CN=user, OU=org, C=US"
    normal_dn = dn.replace(", ", ",")
    form_data = {"distinguished_name": dn}

    form = UserAdminChangeForm(instance=user, data=form_data, prefix=None)

    form.full_clean()
    assert form.instance.distinguished_name is not None
    assert form.instance.distinguished_name != dn
    assert form.instance.distinguished_name == normal_dn
