import functools
from pathlib import Path


def optpass(f):
    @functools.wraps(f)
    def fpass(x):
        if x is None:
            return x
        else:
            return f(x)

    return fpass


opt_str = optpass(str)

opt_path = optpass(Path)

opt_int = optpass(int)
