import functools

import click

from .core import set_interactive, set_verbosity


def option_verbosity(f):
    @click.option("-v", "--verbose", count=True, help="Increase verbosity of output (repeatable).")
    @functools.wraps(f)
    def wrapped(**kwargs):
        verbose = kwargs.pop("verbose")
        set_verbosity(verbose)
        return f(**kwargs)

    return wrapped


def option_interactive(f):
    @click.option("--interactive", "interactive", flag_value=1, help="Force interactive mode.")
    @click.option(
        "--non-interactive", "interactive", flag_value=0, help="Force non-interactive mode."
    )
    @click.option(
        "--detect-interactive",
        "interactive",
        flag_value=-1,
        default=True,
        help="Set interactive mode based on TTY detection (default).",
    )
    @functools.wraps(f)
    def wrapped(**kwargs):
        interactive = kwargs.pop("interactive")
        set_interactive(int(interactive))
        return f(**kwargs)

    return wrapped
