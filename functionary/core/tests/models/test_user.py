import pytest

from core.models import User


@pytest.fixture
def user():
    return User.objects.create(username="testuser")


@pytest.mark.django_db
def test_user_preferences(user):
    """Test set and get of user preferences"""
    assert user.preferences == {}

    # Set the test preference, don't save
    user.set_preference("test", "success")
    assert user.get_preference("test") == "success"

    # Refresh from the database, verify the save didn't occur
    user.refresh_from_db()
    assert user.preferences == {}

    # Set the preference and save it
    user.set_preference("test", "success", save=True)
    user.refresh_from_db()

    assert user.get_preference("test") == "success"
