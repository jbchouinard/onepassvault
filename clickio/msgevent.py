import queue
import re
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from threading import Thread
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.text import Text

from .core import get_verbosity, is_interactive


class MessageBodyType(IntEnum):
    STR = 0
    BYTES = 1
    ANSI = 2
    RICH = 3


@dataclass
class MessageBody:
    data: Any
    type: MessageBodyType = field(init=False)

    def is_bytes(self):
        return self.type == MessageBodyType.BYTES

    def as_bytes(self):
        if self.is_bytes():
            return self.data
        else:
            return str(self).encode("utf-8")

    def __str__(self):
        "Returns unstyled string"
        if self.type == MessageBodyType.STR:
            return self.data
        elif self.type == MessageBodyType.BYTES:
            raise TypeError("binary message cannot be converted to str safely")
        elif self.type == MessageBodyType.ANSI:
            return str(Text.from_ansi(self.data))
        elif self.type == MessageBodyType.RICH:
            return str(self.data)

    def __post_init__(self):
        if isinstance(self.data, Text):
            self.type = MessageBodyType.RICH
        elif isinstance(self.data, bytes):
            self.type = MessageBodyType.BYTES
        elif isinstance(self.data, str):
            if "\x1b[0m" in self.data:
                self.type = MessageBodyType.ANSI
            else:
                self.type = MessageBodyType.STR
        else:
            raise TypeError(f"{type(self.data)} not a supported message")


class Intent(IntEnum):
    INFO = 0
    OUT = 1
    ERR = 2


class Destination(str, Enum):
    LOGGING = "logging"
    STDOUT = "stdout"
    STDERR = "stderr"
    NULL = "null"


@dataclass
class Message:
    intent: Optional[Intent]
    body: Optional[MessageBody] = None
    newline: bool = True
    verbosity: int = 0


class ByteWriteError(Exception):
    pass


class MessageWriter(ABC):
    @abstractmethod
    def write(self, message: Message):
        pass

    @abstractmethod
    def writes_bytes(self) -> bool:
        pass


class ConsoleWriter(MessageWriter):
    def __init__(self, stream):
        self.console = Console(file=stream)

    def writes_bytes(self) -> bool:
        return False

    def write(self, message: Message):
        nl = "\n" if message.newline else ""
        if message.body.type == MessageBodyType.BYTES:
            raise ByteWriteError(str(self))
        elif message.body.type == MessageBodyType.ANSI:
            self.console.print(Text.from_ansi(message.body.data), end=nl)
        else:
            self.console.print(message.body.data, end=nl)


class TextIOWriter(MessageWriter):
    def __init__(self, stream, flush=True):
        self.stream = stream
        self.flush = flush

    def writes_bytes(self) -> bool:
        return hasattr(self.stream, "buffer")

    def write(self, message: Message):
        if message.body.is_bytes():
            try:
                self.stream.buffer.write(message.body.data)
                if message.newline:
                    self.stream.buffer.write(b"\n")
            except AttributeError:
                raise ByteWriteError(str(self))
        else:
            self.stream.write(str(message.body))
            if message.newline:
                self.stream.write("\n")

        if self.flush:
            self.stream.flush()


class NullWriter(MessageWriter):
    def write(self, message: Message):
        pass


class MessageSender(ABC):
    @abstractmethod
    def send(self, message: Message) -> None:
        pass

    def finish(self) -> None:
        pass


def open_file(name: str):
    if name == "stdout":
        return sys.stdout
    elif name == "stderr":
        return sys.stderr
    else:
        return open(name, "w")


def make_writer(destination: str) -> List[MessageWriter]:
    if destination == "null":
        return [NullWriter]
    elif m := re.match(r"console\[(.*)\]$", destination):
        file = open_file(m.group(1))
        return [ConsoleWriter(file), TextIOWriter(file)]
    else:
        return [TextIOWriter(open_file(destination))]


@dataclass
class OutputModeConfig:
    info: str
    out: str
    err: str


@dataclass
class OutputConfig:
    non_interactive: OutputModeConfig = OutputModeConfig(
        info="console[stderr]",
        out="console[stdout]",
        err="console[stderr]",
    )
    interactive: OutputModeConfig = OutputModeConfig(
        info="console[stdout]",
        out="console[stdout]",
        err="console[stderr]",
    )


def make_writers(conf: OutputConfig) -> Dict[Intent, List[MessageWriter]]:
    mconf = conf.interactive if is_interactive(sys.stdout) else conf.non_interactive
    return [
        make_writer(mconf.info),
        make_writer(mconf.out),
        make_writer(mconf.err),
    ]


class MessageRouter(MessageSender):
    def __init__(self, conf: OutputConfig):
        self.verbosity = get_verbosity()
        self.writers = make_writers(conf)

    def send(self, message: Message):
        if message.verbosity > self.verbosity:
            return
        if message.body is None:
            return

        for writer in self.writers[message.intent]:
            if message.body.is_bytes() and not writer.writes_bytes():
                continue
            else:
                writer.write(message)
                break


class MessageQueue(MessageSender):
    def __init__(self, q: queue.SimpleQueue, t: Thread):
        self.q = q
        self.t = t

    def send(self, message: Message):
        self.q.put(message)

    def finish(self):
        self.q.put(None)
        self.t.join()


class MessageRouterWorker(MessageRouter, Thread):
    def __init__(self, q: queue.SimpleQueue, conf: OutputConfig):
        super().__init__(conf)
        Thread.__init__(self)
        self.q = q

    def run(self):
        while True:
            message = self.q.get()
            if message is None:
                return
            else:
                self.send(message)


def init_sender(threadsafe: bool, conf: OutputConfig) -> MessageSender:
    if threadsafe:
        q = queue.SimpleQueue()
        worker = MessageRouterWorker(q, conf)
        worker.start()
        sender = MessageQueue(q, worker)
        return sender
    else:
        return MessageRouter(conf)
