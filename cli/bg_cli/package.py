import importlib
import pathlib
import tarfile
from typing import Tuple

import click
import requests
import yaml

ParamTuple = Tuple[str, str, str]
param_types = ["string", "int", "float", "bool"]


def create_languages() -> list[str]:
    spec = importlib.util.find_spec("bg_cli.create")
    langs = [
        pkg.name[:-3]
        for loc in spec.submodule_search_locations
        for pkg in pathlib.Path(loc).glob(r"[a-zA-Z]*.py")
    ]

    return langs


def enterParams() -> ParamTuple:
    click.echo()
    click.echo("Enter Parameter:")
    name = click.prompt("Name")
    type = click.prompt("Type", type=click.Choice(param_types), show_default=False)
    value = click.prompt("Default Value")

    click.echo()
    return (name, type, value)


def formatParams(params: list[ParamTuple]) -> list:
    return [{"name": x[0], "type": x[1], "defaultValue": x[2]} for x in params]


def generateYaml(output_dir: str, name: str, language: str, params: list[ParamTuple]):
    metadata = {
        "name": name,
        "version": "1.0",
        "language": language,
        "parameters": formatParams(params),
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
@click.option("--simple", "-s", is_flag=True, default=False)
@click.argument("name", type=str)
@click.pass_context
def create_cmd(ctx, simple, language, name, output_directory):
    '''
    Generate a function.

    Create an example function in the specified language.
    '''
    params = []
    body = None
    if simple:
        while click.confirm(
            f"Enter a{'nother' if len(params) > 0 else ''} function parameter?"
        ):
            params.append(enterParams())

        click.echo()
        body = None
        if click.confirm("Enter the function body?", default=True):
            body = click.prompt("Enter Body:\n", prompt_suffix="")

    click.echo()
    create = importlib.import_module(f".{language}", "bg_cli.create")
    if create.generate(output_directory, name, params, body):
        generateYaml(output_directory, name, language, params)


@package_cmd.command()
@click.option("--token", "-t", envvar="BG_TOKEN")
@click.argument("path", type=click.Path(exists=True))
@click.argument("host")
@click.pass_context
def publish(ctx, token, path, host):
    '''
    Create an archive from the project and publish to the build server.

    This will create an archive of the files at the given path and
    then publish them to the build server for image creation.
    Use the -t option to specify a token or set the BG_TOKEN
    environment variable after logging in to *eerGarden.
    '''
    full_path = pathlib.Path(path).resolve()
    tarfile_name = full_path.joinpath(f"{full_path.name}.tar.gz")

    with tarfile.open(str(tarfile_name), "w:gz") as tar:
        tar.add(str(full_path))

    click.echo(f"Publish {str(tarfile_name)} Package at {path} to {host}")

    # publish should http the tar to a server, wait for return
    upload_file = open(tarfile_name, "rb")
    upload_response = None
    headers = {"Authentication": f"Bearer {token}"}
    print(f"Headers: {headers!r}")

    try:
        upload_response = requests.post(
            host, headers=headers, files={"build_file": upload_file}
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
            f"\tResponse: {upload_response.text}",
        )
        ctx.exit(1)
