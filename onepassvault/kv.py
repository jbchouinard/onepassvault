from dataclasses import dataclass
from enum import IntEnum


class Confidentiality(IntEnum):
    PUBLIC = 0
    SECRET = 50


class Visibility(IntEnum):
    HIDDEN = 0
    PLAIN = 1


class Mutability(IntEnum):
    IMMUTABLE = 0
    MUTABLE = 1


class Field:
    def __init__(self, visibility=Visibility.PLAIN, getter=None, setter=None):
        self.visibility = visibility
        self.getter = getter
        self.setter = setter


@dataclass
class DocumentModelConfig:
    confidentiality: Confidentiality
    mutability: Mutability


class DocumentModel:
    pass


class VaultConfig(DocumentModel):
    pass
