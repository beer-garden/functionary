import click

from functionary.config import config_cmd
from functionary.environment import environment_cmd
from functionary.login import login_cmd
from functionary.package import package_cmd


@click.group()
@click.version_option()
def cli():
    pass


cli.add_command(login_cmd)
cli.add_command(package_cmd)
cli.add_command(environment_cmd)
cli.add_command(config_cmd)

if __name__ == "__main__":
    cli()
