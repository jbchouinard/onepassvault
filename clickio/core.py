_verbosity = 0


def set_verbosity(n: int):
    global _verbosity
    _verbosity = int(n)


def get_verbosity() -> int:
    global _verbosity
    return _verbosity


DETECT_TTY = object()

_interactive = DETECT_TTY


def set_interactive(v) -> bool:
    global _interactive
    _interactive = {-1: DETECT_TTY, 0: False, 1: True}.get(v, v)


def is_interactive(stream):
    global _interactive
    if _interactive is DETECT_TTY:
        try:
            return stream.isatty()
        except Exception:
            return False
    else:
        return _interactive
