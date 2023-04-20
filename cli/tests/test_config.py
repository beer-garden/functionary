from click.testing import CliRunner

from functionary.config import config_cmd, get_config_value, get_pool_config


def test_config_set_value():
    """The config command can set a valid setting value"""
    runner = CliRunner()
    setting = "token"
    value = "testvalue"

    assert get_config_value(setting) != value

    runner.invoke(config_cmd, [setting, value])

    assert get_config_value(setting) == value


def test_config_invalid_setting_raises_error():
    """The config command raises an error for unsupported settings"""
    runner = CliRunner()
    setting = "invalid"
    value = "testvalue"

    result = runner.invoke(config_cmd, [setting, value])

    assert "Error" in result.output
    assert get_config_value(setting) is None


def test_config_get_value():
    """The config command with --get displays the current value of a setting"""
    runner = CliRunner()
    setting = "token"
    expected_value = get_config_value(setting)

    result = runner.invoke(config_cmd, ["--get", setting])

    assert result.output.strip() == expected_value


def test_get_pool_config():
    """The config command can set a valid setting value"""
    runner = CliRunner()
    setting = "cert"
    value = "testvalue"

    assert len(get_pool_config()) == 0

    runner.invoke(config_cmd, [setting, value])

    pool_config = get_pool_config()
    assert len(pool_config) == 1
    assert pool_config["cert_file"] == value
