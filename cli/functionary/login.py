import click

from .config import save_config_value
from .tokens import login


@click.command("login")
@click.option("--user", "-u", prompt=True)
@click.password_option(confirmation_prompt=False)
@click.argument("host", type=str)
@click.pass_context
def login_cmd(ctx, user, password, host):
    """
    Login to Functionary.

    Set the output of this command to the FUNCTIONARY_TOKEN environment variable
    for other functionary commands to use to communicate with the server.
    """
    login_url = f"{host}/api/v1/api-token-auth"
    token = login(login_url, user, password)
    save_config_value("token", token)
    save_config_value("host", host)
    click.echo("Login successful!")