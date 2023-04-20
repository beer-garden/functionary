"""Tests Workflow update views"""

import pytest
from django.test.client import Client
from django.urls import reverse

from core.models import Environment, Team, User, Workflow


@pytest.fixture
def environment():
    team = Team.objects.create(name="team")
    return team.environments.get()


@pytest.fixture
def user():
    return User.objects.create(username="user")


@pytest.fixture
def workflow(environment: Environment, user: User):
    return Workflow.objects.create(
        name="workflow1", creator=user, environment=environment, active=True
    )


@pytest.fixture
def other_workflow(environment: Environment, user: User):
    return Workflow.objects.create(
        name="not_workflow1", creator=user, environment=environment, active=True
    )


@pytest.mark.django_db
def test_update_status_archive(admin_client: Client, workflow: Workflow):
    assert workflow.active

    session = admin_client.session
    session["environment_id"] = str(workflow.environment.id)
    session.save()

    url = reverse("ui:workflow-update-status", kwargs={"pk": workflow.id})
    response = admin_client.post(url, {"status": "ARCHIVED"})

    assert response.status_code == 302
    workflow.refresh_from_db()

    assert not workflow.active


@pytest.mark.django_db
def test_update_status_unarchive(admin_client: Client, workflow: Workflow):
    session = admin_client.session
    session["environment_id"] = str(workflow.environment.id)
    session.save()

    workflow.active = False
    workflow.save()

    url = reverse("ui:workflow-update-status", kwargs={"pk": workflow.id})
    response = admin_client.post(url, {"status": "ACTIVE"})

    assert response.status_code == 302
    workflow.refresh_from_db()

    assert workflow.active


@pytest.mark.django_db
def test_update_status_returns_400(admin_client: Client, workflow: Workflow):
    session = admin_client.session
    session["environment_id"] = str(workflow.environment.id)
    session.save()

    url = reverse("ui:workflow-update-status", kwargs={"pk": workflow.id})
    response = admin_client.post(url, {"status": "invalid"})

    assert response.status_code == 400


@pytest.mark.django_db
def test_duplicate_name_fails(
    mocker,
    admin_client: Client,
    workflow: Workflow,
    other_workflow: Workflow,
):
    """Make sure the unique constraint runs on the form validation"""

    session = admin_client.session
    session["environment_id"] = str(other_workflow.environment.id)
    session.save()

    url = reverse("ui:workflow-update", kwargs={"pk": other_workflow.id})

    data = {
        "name": workflow.name,
        "environment": other_workflow.environment.id,
    }

    response = admin_client.post(
        url,
        data=data,
    )
    assert response is not None
    assert response.status_code == 200
    assert (
        "Workflow with this Environment and Name already exists"
        in response.rendered_content
    )
