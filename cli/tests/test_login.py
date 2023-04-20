from unittest.mock import Mock

import urllib3
from click.testing import CliRunner

from functionary.config import get_config_value
from functionary.login import login_cmd


def response_200(*args, **kwargs):
    response = Mock()
    response.status = 200
    response.data = b'{"token": "somegreattoken"}'

    return response


def response_400(*args, **kwargs):
    response = Mock()
    response.status = 400
    response.data = b'{"details": "invalid username or password"}'

    return response


def test_login(monkeypatch):
    """Successful login should update the config"""
    monkeypatch.setattr(urllib3.PoolManager, "request", response_200)
    host = "http://test:1234"

    assert get_config_value("host") != host

    runner = CliRunner()
    result = runner.invoke(login_cmd, ["-u", "user", host], input="password")

    assert result.exit_code == 0
    assert "success" in result.output
    assert get_config_value("host") == host


def test_login_failed(monkeypatch):
    """A failed login attempt should not update the config"""
    monkeypatch.setattr(urllib3.PoolManager, "request", response_400)
    existing_host = get_config_value("host")

    runner = CliRunner()
    result = runner.invoke(
        login_cmd, ["-u", "user", "http://test:1234"], input="password"
    )

    assert result.exit_code == 1
    assert "invalid" in result.output
    assert get_config_value("host") == existing_host
