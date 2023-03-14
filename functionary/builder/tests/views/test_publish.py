import io
import tarfile

import pytest
from django.test.client import MULTIPART_CONTENT
from django.urls import reverse

from core.models import Environment, Team


@pytest.fixture
def environment() -> Environment:
    team = Team.objects.create(name="team")
    return team.environments.get()


@pytest.fixture
def request_headers(environment: Environment) -> dict:
    return {"HTTP_X_ENVIRONMENT_ID": str(environment.id)}


@pytest.fixture
def package_tarball_with_malformed_yaml() -> io.BytesIO:
    malformed_yaml = "somelist:\n"
    malformed_yaml += "  - entry\n"
    malformed_yaml += "- underindented entry"

    package_tarball = io.BytesIO()

    tarinfo = tarfile.TarInfo(name="package.yaml")
    tarinfo.size = len(malformed_yaml)

    with tarfile.open(fileobj=package_tarball, mode="w") as tarball:
        tarball.addfile(tarinfo, io.BytesIO(malformed_yaml.encode()))

    package_tarball.seek(0)

    return package_tarball


def test_publish_returns_400_for_malformed_yaml(
    admin_client, request_headers, package_tarball_with_malformed_yaml
):
    """publish should return a 400 if the package.yaml is malformed"""
    url = reverse("publish")

    input = {"package_contents": package_tarball_with_malformed_yaml}

    response = admin_client.post(
        url, data=input, content_type=MULTIPART_CONTENT, **request_headers
    )

    assert response.status_code == 400
