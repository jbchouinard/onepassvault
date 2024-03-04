import sys

import click

from onepassvault.credentials import start
from onepassvault.userio import echo, interactive, verbosity
from onepassvault.vault import assert_vault_is_live


@click.command()
@click.option("-v", "--verbose", count=True)
@click.option("--noninteractive", is_flag=True)
def cli(verbose, noninteractive):
    verbosity(verbose)
    if noninteractive:
        interactive(False)

    echo(f"Running in {'' if interactive() else 'non-'}interactive mode", 2)
    try:
        op, vault = start()
        assert op.account is not None
        assert_vault_is_live(vault)
    except Exception as e:
        echo(e, color="red", bold=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
