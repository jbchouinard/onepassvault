import os
import sys
import traceback

import click

from clickio.option import option_interactive, option_verbosity
from clickio.output import echo_err, setup_messaging
from clickio.style import Style, set_err_style
from onepassvault.credentials import start
from onepassvault.vault import assert_vault_is_live

OPV_TRACEBACKS = bool(int(os.getenv("OPV_TRACEBACKS", "0")))


set_err_style(Style(fg="red", bold=True))


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option("0.1.0")
@option_verbosity
@option_interactive
def cli():
    setup_messaging()
    try:
        op, vault = start()
        assert op.account is not None
        assert_vault_is_live(vault)
    except Exception as e:
        if OPV_TRACEBACKS:
            traceback.print_exc()
        echo_err(str(e))
        sys.exit(1)


if __name__ == "__main__":
    cli()
