import click
from click.testing import CliRunner

from functionary import environment
from functionary.config import save_config_value


def get_teams_mock(teams):
    return [
        {
            "id": "29f146e9-4fd0-4cd1-b02d-68c75679c144",
            "name": "FunctionFoundry",
            "environments": [
                {"id": "2d113b21-bf1f-4c74-ba12-e37d8f34b72a", "name": "prod"}
            ],
        }
    ]


def user_response_mock(prompt, type=int):
    return 1


def test_set(monkeypatch):
    monkeypatch.setattr(environment, "get", get_teams_mock)
    monkeypatch.setattr(click, "prompt", user_response_mock)
    runner = CliRunner()
    result = runner.invoke(environment.set)
    assert "FunctionFoundry" in result.output


def test_list(monkeypatch):
    monkeypatch.setattr(environment, "get", get_teams_mock)
    id = "3764e110-2e14-4ab6-a8be-ee7b5b6345d6"
    save_config_value("current_environment_id", id)

    runner = CliRunner()
    result = runner.invoke(environment.list)
    assert "FunctionFoundry" in result.output
