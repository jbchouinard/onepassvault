import sys

import click

_verbosity = 0

_interactive = sys.__stdin__.isatty()


def verbosity(n=None) -> int:
    global _verbosity
    if n is not None:
        _verbosity = n
    return _verbosity


def interactive(b=None) -> bool:
    global _interactive
    if b is not None:
        _interactive = bool(b)
    return _interactive


def echo(message="", verbosity=0, color=None, bold=False, indent=0, nl=True):
    message = str(message)
    if indent:
        message = " " * indent + message
    if verbosity > _verbosity:
        return
    if color or bold:
        message = click.style(message, fg=color, bold=bold)
    click.echo(message, nl=nl)


def input_str(prompt, default="", color=None, bold=False, indent=0) -> str:
    if not _interactive:
        return default
    echo(f"{prompt} [{default}]: ", color=color, bold=bold, indent=indent, nl=False)
    return input().strip() or default


def input_bool(prompt, default=True, color=None, bold=False, indent=0) -> bool:
    if not _interactive:
        return default
    ind = "[Y/n]" if default else "[y/N]"
    echo(f"{prompt} {ind}: ", color=color, bold=bold, indent=indent, nl=False)
    yn = input().strip()
    if not yn:
        return default
    return yn.lower() in {"y", "yes"}
