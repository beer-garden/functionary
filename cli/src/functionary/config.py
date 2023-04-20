from pathlib import Path

import click
from dotenv import dotenv_values, set_key

functionary_dir = Path.home() / ".functionary"
config_file = functionary_dir / "config"


def _get_key(key: str):
    config = dotenv_values(dotenv_path=config_file)
    return config.get(key, None)


def save_config_value(key, value):
    """
    Save configuration key and value to config file. If key is already present,
    overwrite the current value.

    Args:
        key: the configuration parameter to set
        value: the value to set the configutation parameter to

    Returns:
        None

    Raises:
        ClickException: Received a PermissionError when opening config file
    """
    try:
        if not functionary_dir.exists():
            functionary_dir.mkdir()

        set_key(
            config_file,
            key,
            value,
        )
    except PermissionError:
        raise click.ClickException(f"Failed to open {config_file}: Permission Denied")


def get_config_value(key, raise_exception=False):
    """
    Retrieve the value associated with a key from the config file

    Args:
        key: the configuration parameter to retrieve the value of
        raise_exception: True to raise an exception if the key has no value

    Returns:
        Value associated with that key as a string

    Raises:
        ClickException: Received PermissionError when opening file or no configuration
        parameter matching the provided key exists
    """
    try:
        value = _get_key(key)
        if value is None:
            if raise_exception is False:
                return None
            else:
                raise click.ClickException(f"Could not find value for {key}")
        else:
            return value
    # if path not found or key not found, raise error
    except PermissionError:
        raise click.ClickException(f"Failed to open {config_file}: Permission Denied")


@click.command("config")
@click.option("--get", is_flag=True, help="View the setting's current value.")
@click.argument("setting", type=str)
@click.argument("value", type=str, required=False)
def config_cmd(get, setting, value):
    """
    Configure a setting

    Set the specified setting to the provided value in your local config
    ($HOME/.functionary/config). Use this to set your authentication token, client
    certificate, or other necessary values.

    \b
    Valid Settings:
        cert:  Client certificate to include on requests to the API
        host:  The base URL for Functionary
        token: API token to use for authentication
    """
    valid_settings = ["cert", "host", "token"]

    if setting not in valid_settings:
        raise click.ClickException(f"Invalid setting: {setting}")

    if get is True:
        click.echo(get_config_value(setting))
    else:
        if value is None:
            raise click.ClickException("Missing argument 'VALUE'.")

        save_config_value(setting, value)


def get_pool_config():
    pool_kwargs = {}

    if cert_file := get_config_value("cert"):
        pool_kwargs["cert_file"] = cert_file

    return pool_kwargs
