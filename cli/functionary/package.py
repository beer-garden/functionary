import os
import pathlib
import shutil
import sys
import tarfile

import click
import yaml
from rich.console import Console
from rich.text import Text

from .client import get, post
from .config import get_config_value
from .parser import parse
from .utils import check_changes, flatten, format_results, sort_functions_by_package


def create_languages() -> list[str]:
    spec = pathlib.Path(__file__).parent.resolve() / "templates"
    return [loc.name for loc in spec.glob("*") if loc.is_dir()]


def generateYaml(output_dir: str, name: str, language: str):
    package_path = pathlib.Path(output_dir).resolve() / name / "package.yaml"
    template_path = (
        pathlib.Path(__file__).parent.resolve() / "templates" / "package.yaml"
    )

    with template_path.open(mode="r") as temp, package_path.open(mode="w") as new:
        filedata = temp.read()
        filedata = filedata.replace("__PACKAGE_LANGUAGE__", language)
        filedata = filedata.replace("__PACKAGE_NAME__", name)
        new.write(filedata)


@click.group("package")
@click.pass_context
def package_cmd(ctx):
    pass


@package_cmd.command("create")
@click.option(
    "--language",
    "-l",
    type=click.Choice(create_languages(), case_sensitive=False),
    required=True,
    prompt="Select the language",
)
@click.argument("name", type=str)
@click.option("--output-directory", "-o", type=click.Path(exists=True), default=".")
@click.pass_context
def create_cmd(ctx, language, name, output_directory):
    """
    Generate a function.

    Create an example function in the specified language.
    """
    if "/" in name:
        ex_path, ex_name = name.rsplit("/", 1)
        raise click.ClickException(
            "Your package name looks like a path. Try using this command instead:"
            f"\n       functionary package create -l {language} -o {ex_path} {ex_name}"
        )
    dir = pathlib.Path(output_directory) / name
    if not dir.exists():
        dir.mkdir()

    elif os.listdir(dir):
        raise click.ClickException(
            f"Create command failed: {output_directory + '/' + name} is not empty."
            "Destination must be a new or empty directory."
        )

    basepath = pathlib.Path(__file__).parent.resolve() / "templates" / language

    shutil.copytree(str(basepath), str(dir), dirs_exist_ok=True)
    generateYaml(output_directory, name, language)

    click.echo()
    click.echo(f"Package creation for {name} successful!\n")
    text = Text()
    console = Console()
    text.append("Next Steps\n", style="b u blue")
    text.append("* ", style="b blue")
    text.append("Write your functions in the generated functions.py\n")
    text.append("* ", style="b blue")
    text.append("Update the package.yaml with your package and function information\n")
    text.append("* ", style="b blue")
    text.append("When ready, publish the package to your environment by running:\n\n")
    text.append(
        f"    functionary package publish {output_directory}/{name}\n", style="b"
    )
    console.print(text)


@package_cmd.command()
@click.argument("path", type=click.Path(exists=True))
@click.option(
    "--keep",
    "-k",
    is_flag=True,
    help="Keep build artifacts after publishing, rather than cleaning them up",
)
@click.option(
    "-y",
    "skip_confirm",
    is_flag=True,
    help="Bypass confirmation of changes and immediately publish",
)
@click.pass_context
def publish(ctx, path, keep, skip_confirm):
    """
    Publish a package to make it available in the currently active environment.

    Use the -k option to keep the build artifacts
    (found in $HOME/.functionary/builds) after publishing,
    rather than cleaning it up.

    Use the -y flag to bypass the confirmation of changes and publish.
    """
    validate_package(path)
    changes = check_changes(path + "/package.yaml")
    if not changes:
        print("There were no changes.")
    if not skip_confirm:
        confirm = input("Continue [y|N]? ").lower()
        if confirm not in ("y", "yes"):
            sys.exit(1)
    host = get_config_value("host", raise_exception=True)
    full_path = pathlib.Path(path).resolve()
    tar_path = get_tar_path(full_path.name)

    with tarfile.open(str(tar_path), "w:gz") as tar:
        tar.add(str(full_path), arcname="")

    with open(tar_path, "rb") as upload_file:
        click.echo(f"Publishing {str(tar_path)} package to {host}")
        response = post("publish", files={"package_contents": upload_file})
        if keep is False:
            os.remove(tar_path)
        id = response["id"]
        click.echo(f"Package upload complete\nBuild id: {id}")


def validate_package(path):
    if not os.path.exists(path + "/package.yaml"):
        raise click.ClickException("No package.yaml in " + path)


def get_tar_path(tar_name):
    """Construct the path to the package tarball"""
    tar_name = tar_name + ".tar.gz"
    tar_path = pathlib.Path.joinpath(pathlib.Path.home(), ".functionary")
    pathlib.Path(tar_path, "builds").mkdir(parents=True, exist_ok=True)
    return pathlib.Path.joinpath(tar_path, "builds", tar_name)


@package_cmd.command()
@click.pass_context
@click.option("--id", help="check the status of a specific build with a given id")
def buildstatus(ctx, id):
    """
    View status for all builds, or the build with a specific id
    """
    title = "Build Status"
    if id:
        results = [get(f"builds/{id}")]
        title = f"Build: {id}"
    else:
        results = get("builds")

    format_results(
        flatten(
            results,
            object_fields={
                "package": [("name", "package"), ("id", "Package ID")],
                "creator": [("username", "creator")],
            },
        ),
        title=title,
        excluded_fields=["environment"],
    )


@package_cmd.command()
@click.pass_context
def list(ctx):
    """
    View all current packages and their functions
    """
    packages = get("packages")
    functions = get("functions")
    function_lookup = sort_functions_by_package(functions)

    for package in packages:
        name = package["name"]
        id = package["id"]
        # Use the description since there's more room if it's available,
        # otherwise use the summary
        if not (package_description := package.get("description", None)):
            package_description = package["summary"]

        associated_functions = []
        for function in function_lookup[id]:
            function_dict = {}
            function_dict["Function"] = function["name"]
            function_dict["Display Name"] = function["display_name"]

            # Use the summary if available to keep the table tidy, otherwise
            # use the description
            if not (function_description := function.get("summary", None)):
                function_description = function["description"]
            function_dict["Description"] = (
                function_description if function_description else ""
            )
            associated_functions.append(function_dict)

        title = Text(f"{name}", style="bold blue")

        # Don't show if there's no package summary or description
        if package_description:
            title.append(f"\n{package_description}", style="blue dim")
        format_results(associated_functions, title=title)
        click.echo("\n")


@package_cmd.command()
@click.pass_context
@click.argument("path", type=str)
def genschema(ctx, path):
    """
    Populate package.yaml with package functions
    """

    language = None
    try:
        with open(path + "/package.yaml", "r") as yaml_file:
            filedata = yaml.safe_load(yaml_file)
            language = filedata["package"]["language"]
    except FileNotFoundError:
        raise click.ClickException("Could not find package.yaml file")
    except PermissionError:
        raise click.ClickException("Did not have permission to access package.yaml")
    except NotADirectoryError:
        raise click.ClickException(f"Directory {path} does not exist")

    functions = parse(language, path)

    if len(functions) == 0:
        click.echo("No functions detected, package.yaml unchanged")
    else:
        try:
            filedata["package"]["functions"] = functions

            with open(path + "/package.yaml", "w") as yaml_file:
                yaml.dump(filedata, yaml_file, sort_keys=False)
        except FileNotFoundError:
            raise click.ClickException("Could not find package.yaml file")
        except PermissionError:
            raise click.ClickException("Did not have permission to access package.yaml")

        click.echo("Package.yaml successfully updated!")
