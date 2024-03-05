import signal
import sys
from typing import Callable, List

from .msgevent import Intent, Message, MessageBody, OutputConfig, init_sender

try:
    import colorama

    colorama.just_fix_windows_console()
except ImportError:
    pass


_sender = None


def setup_messaging(threadsafe: bool = False, conf=OutputConfig()):
    global _sender
    if _sender is not None:
        raise Exception("init_messaging must only be called once")
    _sender = init_sender(threadsafe, conf)


def install_signal_handlers():
    def _handle_sigint(signum, frame):
        teardown_messaging()
        raise KeyboardInterrupt()

    def _handle_sigterm(signum, frame):
        teardown_messaging()
        sys.exit(0)

    signal.signal(signal.SIGINT, _handle_sigint)
    signal.signal(signal.SIGTERM, _handle_sigterm)


def teardown_messaging():
    global _sender
    if _sender is not None:
        _sender.finish()
    _sender = None


def send_message(message: Message):
    global _sender
    if _sender is None:
        print("init_messaging must be called before sendin", file=sys.stderr)
    else:
        _sender.send(message)


Hook = Callable[[Message], Message]


def _apply_hooks(hooks: List[Hook], message: str) -> str:
    for func in hooks:
        message = func(message)
    return message


_info_hooks: List[Hook] = []


def install_info_hook(func: Hook):
    global _info_hooks
    _info_hooks.append(func)


def echo_info(message: bytes | str, verbosity=0, nl=True):
    """
    Prints a non-error message intended for humans.

    Supports click.style, and style markup if rich is installed.

    In interactive mode, echo_info prints to stdout.

    In non-interactive mode, echo_info prints to stderr, so that the message
    does not interfere with machine-parseable outputs (e.g. JSON).
    """
    message = Message(
        intent=Intent.INFO, body=MessageBody(message), newline=nl, verbosity=verbosity
    )
    message = _apply_hooks(_info_hooks, message)
    send_message(message)


def echo_info_v(message: bytes | str, nl=True):
    "echo_info with verbosity=1"
    echo_info(message, 1, nl)


def echo_info_vv(message: bytes | str, nl=True):
    "echo_info with verbosity=2"
    echo_info(message, 2, nl)


def echo_info_vvv(message: bytes | str, nl=True):
    "echo_info with verbosity=3"
    echo_info(message, 3, nl)


_out_hooks: List[Hook] = []


def install_out_hook(func: Hook):
    global _out_hooks
    _out_hooks.append(func)


def echo_out(message="", nl=True):
    """
    Prints a message to stdout.

    Supports click.style, and style markup if rich is installed.
    """
    message = Message(intent=Intent.OUT, body=MessageBody(message), newline=nl, verbosity=0)
    message = _apply_hooks(_out_hooks, message)
    send_message(message)


_err_hooks: List[Hook] = []


def install_err_hook(func: Hook):
    global _err_hooks
    _err_hooks.append(func)


def echo_err(message="", nl=True):
    """
    Prints a message to stderr.

    Supports click.style, and style markup if rich is installed.
    """
    message = Message(intent=Intent.ERR, body=MessageBody(message), newline=nl, verbosity=0)
    message = _apply_hooks(_err_hooks, message)
    send_message(message)
