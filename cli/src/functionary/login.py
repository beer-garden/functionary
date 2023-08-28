import click

from .config import save_config_value
from .tokens import login


@click.command("login")
@click.option("--user", "-u", prompt=True)
@click.password_option(confirmation_prompt=False)
@click.argument("host", type=str)
def login_cmd(user, password, host):
    """
    Login to Functionary

    Set the output of this command to the FUNCTIONARY_TOKEN environment variable
    for other functionary commands to use to communicate with the server.
    """
    token = login(host, user, password)
    save_config_value("host", host)
    save_config_value("token", token)
    click.echo("Login successful!")
