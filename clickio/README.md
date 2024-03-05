The `clickio` package is a set of tools meant to help build [`click`](https://pypi.org/project/click/) apps
with rich text I/O, which are easy to use both interactively or in a shell pipeline.

# Features

## Intentional output

The `clickio.output` module contains different output functions for different purposes:
- `echo_info`: print informative messages, intended for humans
- `echo_out`: print program output, intended for humans or machine parsing
- `echo_err`: print error messages

These functions must be used for printing to enable most of the features described below.

## Adaptive user prompts

The` clickio.input` module contains functions for prompting user input:
- `prompt`: Get string input from user (or default value in non-interactive mode, see below)
- `prompt_yn`: Get boolean choice from user (or default value in non-interactive mode, see below)

`PromptOpt` can be used to expose CLI arguments, and prompt the user if they are not passed in:

```python
from clickio.input import PromptOpt

class Opt(PromptOpt):
    vault_addr: str = "http://localhost:8200"
    vault_unseal: bool = False

@click.command()
@Opt().add_options()
def cli(vault_addr, vault_unseal):
    vault_addr: str = vault_addr.get()
    vault_unseal: bool = vault_unseal.get()
```

This is different from `click.option(prompt=True)` in a couple of ways:
- Prompting is lazy, it happens when `get` is called, not during argument parsing
- If the program is not attached to an interactive TTY, prompting is skipped (see below)

## Verbosity

The `clickio.option.option_verbosity` decorator adds and parses a -v/--verbose flag
to a command (which can be given multiple times, e.g. -vvv).

```python
import click
from clickio.option import option_verbosity
from clickio.output import echo_info, echo_info_v, echo_info_vv

@click.command()
@option_verbosity
def my_command():
    # -v flags are parsed automatically, no need to do anything else
    echo_info("This will always be printed")
    echo_info_v("This will be printed if at least -v")
    echo_info_vv("This will be printed if at least -vv")
    echo_info("This will be printed if at least -vv", verbosity=2)
```

The `echo_info` functions accept a `verbosity` argument, which corresponds to
the minimum number of -v flags that must be present for the message to be printed.

There are also convenience functions `echo_info_v`, `echo_info_vv`, `echo_info_vvv`
with a preset verbosity level.

## Styling

The `clickio.style` module contains text styling utilities, with optional integration
with [`rich`](https://pypi.org/project/rich/).

```python
from clickio.style import with_style, Style

# Always works
echo_info(with_style("Hello!", Style(fg="red", bold=true)))
```

If [`rich`](https://pypi.org/project/rich/) is installed, [color markup](https://rich.readthedocs.io/en/latest/markup.html)
is supported.


```python
from clickio.output import echo_info
# Works only if rich is installed
echo_info("[red bold]Hello![/red bold]")
```

Alternatively, `click.style` can be used directly:

```python
import click
# Works if rich is not installed
echo_info(click.style("Hello", fg="red", bold=True))
```

If [`colorama`](https://pypi.org/project/colorama/) is installed, `clickio` will attempt to make styling work on Windows.


## Interactive / non-interactive mode

`clickio` wants to help make programs that are easy to use both when they are attached
to an interactive terminal, and when they are part of a pipeline of commands.

In non-interactive mode, the following adaptations are made:
- prompt functions skip getting user input and just return their defaults
- `echo_info` output is redirected so that downstream piped commands can safely parse the output of `echo_out`
    - To stderr by default, can be changed to /dev/null or logging
- Text styling is not applied

By default, `clickio` tries to detect if the program is attached to an interactive TTY.
The `clickio.option.option_interactive` decorator can be used to add explicit
--interactive/--non-interactive flags to a command:

```python
import json
import click
from clickio.option import option_interactive
from clickio.output import echo_info

@click.command()
@option_interactive
def my_command():
    # Nothing else to do
    echo_out(json.dumps({"message": "this always goes to stdout"}))
    echo_info(
        "This will go to stdout in interactive mode,"
        " or be redirected in non-interactive mode"
        " so that `my_command | jq .` works"
    )
```

## Logging integration
