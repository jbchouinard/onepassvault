import click

VERBOSITY = 0


def echo(message, verbosity=0, color=None, bold=False):
    if verbosity > VERBOSITY:
        return
    if color or bold:
        message = click.style(message, fg=color, bold=bold)
    click.echo(message)


def input_bool(prompt, default=True) -> bool:
    ind = "[Y/n]" if default else "[y/N]"
    yn = input(f"{prompt} {ind}: ")
    if not yn:
        return default
    return yn.lower() in {"y", "yes"}
