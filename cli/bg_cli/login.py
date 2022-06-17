import click
import requests


@click.command("login")
@click.option("--user", "-u", prompt=True)
@click.password_option(confirmation_prompt=False)
@click.argument("host", type=str)
@click.pass_context
def login_cmd(ctx, user, password, host):
    '''
    Login to *eerGarden.

    Set the output of this command to the BG_TOKEN environment variable
    for other bg-cli commands to use to communicate with the server.
    '''
    login_url = f"{host}/login"
    login_response = None
    headers = {"user": user, "password": password}
    click.echo(f"Headers: {headers!r}", err=True)

    try:
        login_response = requests.post(f"{login_url}", headers=headers)
    except requests.ConnectionError:
        click.echo(f"Unable to connect to {login_url}", err=True)
        ctx.exit(2)
    except requests.Timeout:
        click.echo("Timeout occurred waiting for build", err=True)
        ctx.exit(2)

    # check status code/message on return then exit
    if login_response.ok:
        click.echo(login_response.text)
    else:
        click.secho(
            f"Failed to build image: {login_response.status_code}\n"
            f"\tResponse: {login_response.text}",
            err=True,
            fg="red",
        )
        ctx.exit(1)
