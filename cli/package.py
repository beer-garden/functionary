import importlib
import os
import re
from typing import Tuple
import yaml

import click

ParamTuple = Tuple[str, str, str]
param_types = ["string", "int", "float", "bool"]


def create_languages() -> list[str]:
    spec = importlib.util.find_spec("cli.create")
    files = [pkg for loc in spec.submodule_search_locations for pkg in os.listdir(loc)]
    langs = [x[:-3] for x in files if re.match(r"[a-zA-Z]+\.py", x)]

    return langs


def enterParams() -> ParamTuple:
    click.echo("\nEnter Parameter: ")
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
    with open(f"{output_dir}/{name}/{name}.yaml", mode="w") as file:
        file.write(yaml.dump(metadata))


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
    create = importlib.import_module(f".{language}", "cli.create")
    if create.generate(output_directory, name, params, body):
        generateYaml(output_directory, name, language, params)


@package_cmd.command()
@click.argument("path", type=click.Path(exists=True))
def publish(path):
    click.echo(f"Publish Package at {path}")
    # publish should http the tar to a server, wait for return,
    # check status code/message on return then exit
