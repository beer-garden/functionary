import click

from .login import login_cmd
from .package import package_cmd


@click.group()
def cli():
    pass


cli.add_command(login_cmd)
cli.add_command(package_cmd)
