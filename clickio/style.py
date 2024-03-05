from dataclasses import asdict, dataclass

from rich.text import Text

from clickio import output
from clickio.msgevent import Message, MessageBody


@dataclass
class Style:
    fg: str | None = None
    bg: str | None = None
    bold: bool = False
    italic: bool = False
    underline: bool = False
    strikethrough: bool = False
    blink: bool = False
    reverse: bool = False


def with_style(message: Message, style: Style) -> Message:
    adjectives = [
        {"strikethrough": "strike"}.get(k, k) for k, v in asdict(style).items() if v is True
    ]
    if style.fg:
        adjectives.append(style.fg)
    if style.bg:
        adjectives.extend(["on", style.bg])
    adjectives = " ".join(adjectives)

    message.body = MessageBody(Text(str(message.body.data), style=adjectives))
    return message


def style_hook(style: Style):
    def hook(message: str):
        return with_style(message, style)

    return hook


def set_info_style(style: Style):
    output.install_info_hook(style_hook(style))


def set_out_style(style: Style):
    output.install_out_hook(style_hook(style))


def set_err_style(style: Style):
    output.install_err_hook(style_hook(style))
