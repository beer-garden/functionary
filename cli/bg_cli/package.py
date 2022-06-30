import importlib
import pathlib
import tarfile

import click
import requests
import yaml

from .tokens import TokenError, getToken


def create_languages() -> list[str]:
    spec = importlib.util.find_spec("bg_cli.create")
    langs = [
        pkg.name[:-3]
        for loc in spec.submodule_search_locations
        for pkg in pathlib.Path(loc).glob(r"[a-zA-Z]*.py")
    ]

    return langs


def generateYaml(output_dir: str, name: str, language: str):
    metadata = {
        "name": name,
        "version": "1.0",
        "language": language,
    }

    path = pathlib.Path(output_dir).resolve() / name / f"{name}.yaml"
    with path.open(mode="w"):
        path.write_text(yaml.dump(metadata))


@click.group("package")
@click.pass_context
def package_cmd(ctx):
    pass


@package_cmd.command("create")
@click.option(
    "--language",
    "-l",
    type=click.Choice(create_languages(), case_sensitive=False),
    default="python",
)
@click.option("--output-directory", "-o", type=click.Path(exists=True), default=".")
@click.argument("name", type=str)
@click.pass_context
def create_cmd(ctx, language, name, output_directory):
    """
    Generate a function.

    Create an example function in the specified language.
    """
    click.echo()
    create = importlib.import_module(f".{language}", "bg_cli.create")
    if create.generate(output_directory, name):
        generateYaml(output_directory, name, language)


@package_cmd.command()
@click.argument("path", type=click.Path(exists=True))
@click.argument("host")
@click.pass_context
def publish(ctx, path, host):
    """
    Create an archive from the project and publish to the build server.

    This will create an archive of the files at the given path and
    then publish them to the build server for image creation.
    Use the -t option to specify a token or set the BG_TOKEN
    environment variable after logging in to *eerGarden.
    """
    try:
        token = getToken()
    except TokenError as t:
        click.secho(str(t), err=True, fg="red")
        click.echo("Try log in again")
        ctx.exit(2)

    full_path = pathlib.Path(path).resolve()
    tarfile_name = full_path.joinpath(f"{full_path.name}.tar.gz")

    with tarfile.open(str(tarfile_name), "w:gz") as tar:
        tar.add(str(full_path), arcname=".")

    click.echo(f"Publishing {str(tarfile_name)} package to {host}")

    # publish should http the tar to a server, wait for return
    upload_file = open(tarfile_name, "rb")
    upload_response = None
    headers = {"Authorization": f"Bearer {token}"}

    try:
        upload_response = requests.post(
            host, headers=headers, files={"file": upload_file}
        )
    except requests.ConnectionError:
        click.echo(f"Unable to connect to {host}")
        ctx.exit(2)
    except requests.Timeout:
        click.echo("Timeout occurred waiting for build")
        ctx.exit(2)

    # check status code/message on return then exit
    if upload_response.ok:
        click.echo("Build succeeded")
    else:
        click.echo(
            f"Failed to build image: {upload_response.status_code}\n"
            f"\tResponse: {upload_response.text}"
        )
        if upload_response.status_code == 401:
            click.echo("\n\nTry log in again.")
        ctx.exit(1)
