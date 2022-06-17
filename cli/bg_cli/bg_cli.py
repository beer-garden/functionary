import click

from .package import package_cmd


@click.group()
def cli():
    pass


cli.add_command(package_cmd)
