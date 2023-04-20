from io import BytesIO

import pytest
from django.core.files.base import ContentFile
from django.test.client import MULTIPART_CONTENT
from django.urls import reverse

from core.auth import Role
from core.models import EnvironmentUserRole, Team, UserFile


@pytest.fixture
def environment():
    team = Team.objects.create(name="team")
    return team.environments.get()


@pytest.fixture
def user_with_access(django_user_model, environment):
    user = django_user_model.objects.create(username="testuser", password="password")

    EnvironmentUserRole.objects.create(
        user=user,
        environment=environment,
        role=Role.DEVELOPER.name,
    )

    return user


@pytest.fixture
def public_file(environment, admin_user):
    user_file = UserFile(
        environment=environment, creator=admin_user, name="public_file", public=True
    )
    user_file.file.save(user_file.name, ContentFile("public test file"))

    return user_file


@pytest.fixture
def private_file(environment, admin_user):
    user_file = UserFile(
        environment=environment, creator=admin_user, name="private_file", public=False
    )
    user_file.file.save(user_file.name, ContentFile("private test file"))

    return user_file


@pytest.fixture
def personal_file(environment, user_with_access):
    user_file = UserFile(
        environment=environment,
        creator=user_with_access,
        name="personal_file",
        public=False,
    )
    user_file.file.save(user_file.name, ContentFile("personal test file"))

    return user_file


@pytest.fixture
def request_headers(environment):
    return {"HTTP_X_ENVIRONMENT_ID": str(environment.id)}


@pytest.mark.django_db
def test_list_includes_only_owned_and_public_files(
    client, request_headers, user_with_access, public_file, private_file, personal_file
):
    url = reverse("userfile-list")

    client.force_login(user_with_access)
    response = client.get(url, **request_headers)

    response_ids = [result["id"] for result in response.data["results"]]

    assert str(public_file.id) in response_ids
    assert str(personal_file.id) in response_ids
    assert str(private_file.id) not in response_ids


@pytest.mark.django_db
def test_retrieve_public_file(client, request_headers, user_with_access, public_file):
    url = reverse("userfile-detail", kwargs={"pk": str(public_file.id)})

    client.force_login(user_with_access)
    response = client.get(url, **request_headers)

    assert response.status_code == 200
    assert response.data["id"] == str(public_file.id)


@pytest.mark.django_db
def test_retrieve_returns_404_for_private_file(
    client, request_headers, user_with_access, private_file
):
    url = reverse("userfile-detail", kwargs={"pk": str(private_file.id)})

    client.force_login(user_with_access)
    response = client.get(url, **request_headers)

    assert response.status_code == 404


@pytest.mark.django_db
def test_create(client, request_headers, user_with_access):
    url = reverse("userfile-list")
    form_data = {"file": BytesIO(b"files are fun")}

    client.force_login(user_with_access)
    response = client.post(
        url, data=form_data, content_type=MULTIPART_CONTENT, **request_headers
    )

    assert response.status_code == 200
    assert UserFile.objects.filter(id=response.data["id"]).exists()


@pytest.mark.django_db
def test_create_with_missing_file_returns_400(
    client, request_headers, user_with_access
):
    url = reverse("userfile-list")
    form_data = {"public": True}

    client.force_login(user_with_access)
    response = client.post(
        url, data=form_data, content_type=MULTIPART_CONTENT, **request_headers
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_delete_own_file(client, request_headers, user_with_access, personal_file):
    url = reverse("userfile-detail", kwargs={"pk": str(personal_file.id)})

    client.force_login(user_with_access)
    response = client.delete(url, **request_headers)

    assert response.status_code == 204
    assert not UserFile.objects.filter(id=personal_file.id).exists()


@pytest.mark.django_db
def test_delete_other_user_public_file_returns_403(
    client, request_headers, user_with_access, public_file
):
    url = reverse("userfile-detail", kwargs={"pk": str(public_file.id)})

    client.force_login(user_with_access)
    response = client.delete(url, **request_headers)

    assert response.status_code == 403


@pytest.mark.django_db
def test_delete_other_user_private_file_returns_404(
    client, request_headers, user_with_access, private_file
):
    url = reverse("userfile-detail", kwargs={"pk": str(private_file.id)})

    client.force_login(user_with_access)
    response = client.delete(url, **request_headers)

    # 404 expected because private files are not visible per the queryset
    assert response.status_code == 404
