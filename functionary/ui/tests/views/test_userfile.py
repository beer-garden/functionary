from io import BytesIO

import pytest
from django.core.files.base import ContentFile
from django.test.client import MULTIPART_CONTENT, Client
from django.urls import reverse

from core.auth import Role
from core.models import Environment, EnvironmentUserRole, Team, User, UserFile


@pytest.fixture
def environment():
    team = Team.objects.create(name="team")
    return team.environments.get()


@pytest.fixture
def user(environment: "Environment"):
    user = User.objects.create(username="user")
    EnvironmentUserRole.objects.create(
        user=user,
        environment=environment,
        role=Role.DEVELOPER.name,
    )
    return user


@pytest.fixture
def other_user(environment: "Environment"):
    user = User.objects.create(username="other_user")
    EnvironmentUserRole.objects.create(
        user=user,
        environment=environment,
        role=Role.ADMIN.name,
    )
    return user


@pytest.fixture
def public_file(environment, user):
    user_file = UserFile(
        environment=environment, creator=user, name="public_file", public=True
    )
    user_file.file.save(user_file.name, ContentFile("public test file"))

    return user_file


@pytest.fixture
def private_file(environment, user):
    user_file = UserFile(
        environment=environment, creator=user, name="private_file", public=False
    )
    user_file.file.save(user_file.name, ContentFile("private test file"))

    return user_file


@pytest.fixture
def other_public_file(environment, other_user):
    user_file = UserFile(
        environment=environment,
        creator=other_user,
        name="other_public_file",
        public=True,
    )
    user_file.file.save(user_file.name, ContentFile("public test file"))

    return user_file


@pytest.fixture
def other_private_file(environment, other_user):
    user_file = UserFile(
        environment=environment,
        creator=other_user,
        name="other_private_file",
        public=False,
    )
    user_file.file.save(user_file.name, ContentFile("private test file"))

    return user_file


@pytest.mark.django_db
def test_share_file(client: Client, user: User, public_file: UserFile):
    """Check that sharing/protecting a file works"""
    session = client.session
    session["environment_id"] = str(public_file.environment.id)
    session.save()

    url = reverse("ui:file-share", kwargs={"pk": public_file.id})
    client.force_login(user)

    response = client.post(url, {"public": False})

    assert response.status_code == 302
    public_file.refresh_from_db()

    assert not public_file.public

    response = client.post(url, {"public": True})

    assert response.status_code == 302
    public_file.refresh_from_db()

    assert public_file.public


@pytest.mark.django_db
def test_share_file_returns_404(
    client: Client, user: User, other_public_file: UserFile
):
    """Check that users can't share other users files"""
    session = client.session
    session["environment_id"] = str(other_public_file.environment.id)
    session.save()

    url = reverse("ui:file-share", kwargs={"pk": other_public_file.id})
    client.force_login(user)

    response = client.post(url, {"public": False})

    assert response.status_code == 404


@pytest.mark.django_db
def test_update_name(
    client: Client, user: User, public_file: UserFile, other_public_file: UserFile
):
    """Verify that renaming a file works appropriately"""
    session = client.session
    session["environment_id"] = str(public_file.environment.id)
    session.save()

    url = reverse("ui:file-update", kwargs={"pk": public_file.id, "action": "rename"})
    client.force_login(user)

    old_name = public_file.name
    new_name = f"is_{old_name}"
    response = client.post(url, {"name": new_name})

    assert response.status_code == 200
    public_file.refresh_from_db()

    assert public_file.name == new_name

    url = reverse(
        "ui:file-update", kwargs={"pk": other_public_file.id, "action": "rename"}
    )
    client.force_login(user)

    response = client.post(url, {"name": old_name})

    assert response.status_code == 404


@pytest.mark.django_db
def test_update_file(
    client: Client, user: User, public_file: UserFile, other_public_file: UserFile
):
    """Verify that updating a files contents works appropriately"""
    session = client.session
    session["environment_id"] = str(public_file.environment.id)
    session.save()

    new_file_data = b"files are fun"
    form_data = {"file": BytesIO(new_file_data), "name": public_file.name}

    client.force_login(user)
    url = reverse("ui:file-update", kwargs={"pk": public_file.id, "action": "replace"})
    response = client.post(url, data=form_data, content_type=MULTIPART_CONTENT)

    assert response.status_code == 200

    public_file.refresh_from_db()
    assert public_file.file.read() == new_file_data

    url = reverse(
        "ui:file-update", kwargs={"pk": other_public_file.id, "action": "replace"}
    )
    response = client.post(url, data=form_data, content_type=MULTIPART_CONTENT)

    assert response.status_code == 404


@pytest.mark.django_db
def test_list_files(
    client: Client,
    user: User,
    public_file: UserFile,
    private_file: UserFile,
    other_public_file: UserFile,
    other_private_file: UserFile,
):
    """Verify the listing of files.
    - file-list should only return owned files
    - file-table with "owned" file type should only return owned files
    - file-table with "shared" file type should only return other users public files
    """
    session = client.session
    session["environment_id"] = str(public_file.environment.id)
    session.save()

    client.force_login(user)
    url = reverse("ui:file-list")
    response = client.get(url)

    assert response.status_code == 200
    files = list(response.context_data.get("userfile_list").all())
    assert public_file in files
    assert private_file in files
    assert other_public_file not in files
    assert other_private_file not in files

    url = reverse("ui:file-table")
    response = client.get(url, data={"file_type": "owned"})

    assert response.status_code == 200
    files = list(response.context_data.get("userfile_list").all())
    assert public_file in files
    assert private_file in files
    assert other_public_file not in files

    response = client.get(url, data={"file_type": "shared"})

    assert response.status_code == 200
    files = list(response.context_data.get("userfile_list").all())
    assert public_file not in files
    assert private_file not in files
    assert other_public_file in files
    assert other_private_file not in files
