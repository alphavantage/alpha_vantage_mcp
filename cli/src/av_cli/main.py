import click

from av_cli import __version__


@click.group()
@click.version_option(version=__version__, prog_name="av-cli")
def cli():
    """Alpha Vantage CLI."""


if __name__ == "__main__":
    cli()
