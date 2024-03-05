import sys

import click

from .core import is_interactive
from .output import echo_info


def prompt(message: str = "", default: str = "", end: str = ": ") -> str:
    "Gets string input if in interactive mode, else returns default."
    if not is_interactive(sys.stdin):
        return default
    echo_info(f"{message} ({default}){end or ''}", nl=False)
    return input().strip() or default


def prompt_yn(message: str = "", default: bool = True, end: str = ": ") -> bool:
    "Gets yes/no input if in interactive mode, else returns default."
    if not is_interactive(sys.stdin):
        return default
    ind = "(Y/n)" if default else "(y/N)"
    echo_info(f"{message} {ind}{end or ''}", nl=False)
    yn = input().strip()
    if not yn:
        return default
    return yn.lower() in {"y", "yes"}


PROMPT_BY_TYPE = {
    str: prompt,
    bool: prompt_yn,
}


class PromptOptField:
    def __init__(self, name, type, default_value, prompt=None, options=None):
        self.name = name
        self.type = type
        self.default_value = default_value
        self.promptf = prompt or PROMPT_BY_TYPE[type]
        self.options = options or [f"--{name.replace('_', '-')}"]


class PromptOptMeta(type):
    def __new__(metacls, name, bases, attrs):
        annotations = attrs.get("__annotations__", {})
        attrs["__annotations__"] = annotations

        fnames = set(attrs.keys()) | set(annotations.keys())
        fnames = {f for f in fnames if not f.startswith("_")}
        ftypes = [annotations.get(f) for f in fnames]
        fvals = [attrs.get(f) for f in fnames]

        fields = {}
        for name, type_, val in zip(fnames, ftypes, fvals):
            if type_ in PROMPT_BY_TYPE:
                annotations[name] = PromptOptField
                fields[name] = PromptOptField(name, type_, val)

        attrs.update(fields)
        attrs["_prompt_opt_fields"] = fields
        return super().__new__(metacls, name, bases, attrs)


class PromptOptValue:
    def __init__(self, field: PromptOptField):
        self._field = field
        self._arg_value = None
        self._prompt_value = None

    @property
    def __name__(self):
        return self._field.type.__name__

    def __call__(self, val=None):
        if val is self:
            pass
        elif val is not None:
            self._arg_value = self._field.type(val)
        return self

    def get(self):
        if self._arg_value is not None:
            return self._arg_value
        elif self._prompt_value is not None:
            return self._prompt_value
        else:
            return self._field.promptf(self._field.name, self._field.default_value)


class PromptOpt(metaclass=PromptOptMeta):
    def add_options(self):
        def decorator(cmd):
            for field in self._prompt_opt_fields.values():
                pval = PromptOptValue(field)
                cmd = click.option(*field.options, type=pval, default=pval)(cmd)
            return cmd

        return decorator
