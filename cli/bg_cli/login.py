import click

from .tokens import login


@click.command("login")
@click.option("--user", "-u", prompt=True)
@click.password_option(confirmation_prompt=False)
@click.argument("host", type=str)
@click.pass_context
def login_cmd(ctx, user, password, host):
    """
    Login to *eerGarden.

    Set the output of this command to the BG_TOKEN environment variable
    for other bg-cli commands to use to communicate with the server.
    """
    login_url = f"{host}/api/token/"
    login_response = login(login_url, user, password)

    # check status code/message on return then exit
    if login_response["success"]:
        click.echo("Login successful!")
    else:
        click.secho(
            login["message"],
            err=True,
            fg="red",
        )
        ctx.exit(1)
