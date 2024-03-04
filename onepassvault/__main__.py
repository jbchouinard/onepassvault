import sys

import click

import onepassvault.userio
from onepassvault.credentials import start
from onepassvault.userio import echo


@click.command()
@click.option("-v", "--verbose", count=True)
def cli(verbose):
    onepassvault.userio.VERBOSITY = verbose
    try:
        op, vault = start()
        echo(op)
        echo(vault)
    except Exception as e:
        echo(str(e), color="red", bold=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
