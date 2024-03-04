import copy
import json
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel


class OpVault(BaseModel):
    id: str
    name: str
    content_version: Optional[int] = None
    attribute_version: Optional[int] = None
    items: Optional[int] = None
    type: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def __str__(self):
        return f"Vault {self.name} ({self.id})"


class OpItemFieldType(str, Enum):
    PASSWORD = "CONCEALED"
    TEXT = "STRING"
    EMAIL = "EMAIL"
    URL = "URL"
    DATE = "DATE"
    MONTH_YEAR = "MONTH_YEAR"
    PHONE = "PHONE"
    OTP = "OTP"


class OpItemField(BaseModel):
    id: str
    type: OpItemFieldType
    value: Optional[Any] = None
    purpose: Optional[str] = None
    label: Optional[str] = None
    reference: Optional[str] = None

    @classmethod
    def new(
        cls,
        name: str,
        type: OpItemFieldType,
        value: Optional[Any] = None,
        purpose: Optional[Any] = None,
    ) -> "OpItemField":
        return cls(id=name, label=name, type=type, value=value, purpose=purpose)


class OpItem:
    def __init__(self, data: dict):
        self._data = data
        fields = data.pop("fields", [])
        self.fields_by_id = {f["id"]: OpItemField.model_validate(f) for f in fields}
        self.fields_by_label = {f["label"]: OpItemField.model_validate(f) for f in fields}

    @property
    def id(self) -> Optional[str]:
        return self._data.get("id")

    @property
    def category(self) -> str:
        return self._data["category"]

    @property
    def title(self) -> Optional[str]:
        return self._data.get("title")

    @property
    def vault(self) -> Optional[OpVault]:
        if "vault" in self._data:
            return OpVault.model_validate(self._data["vault"])
        else:
            return None

    def add_field(
        self,
        name: str,
        type: OpItemFieldType,
        value: Optional[Any] = None,
        purpose: Optional[Any] = None,
    ) -> OpItemField:
        if name in self.fields_by_id:
            raise ValueError(f"Field {name} already exists on Item {self.id}")
        field = OpItemField.new(name=name, type=type, value=value, purpose=purpose)
        self.set_field(field)
        return field

    def get_field(self, key: str, by_label=True) -> OpItemField:
        fieldmap = self.fields_by_label if by_label else self.fields_by_id
        return fieldmap.get(key)

    def get_field_value(self, key: str, by_label=True) -> Optional[Any]:
        field = self.get_field(key, by_label)
        if field is None:
            return None
        return field.value

    def set_field(self, field: OpItemField):
        self.fields_by_id[field.id] = field
        self.fields_by_label[field.label] = field

    def set_field_value(self, key: str, value: Any, by_label=True):
        fieldmap = self.fields_by_label if by_label else self.fields_by_id
        fieldmap[key].value = value

    def remove_field(self, key: str, by_label=True) -> OpItemField:
        if by_label:
            field = self.fields_by_label.pop(key)
            self.fields_by_id.pop(field.id)
        else:
            field = self.fields_by_id.pop(key)
            self.fields_by_label.pop(field.label)
        return field

    def has_field(self, key: str, by_label=True) -> bool:
        fieldmap = self.fields_by_label if by_label else self.fields_by_id
        return key in fieldmap

    def to_json(self) -> bytes:
        data = copy.deepcopy(self._data)
        data["fields"] = [f.model_dump() for f in self.fields_by_id.values()]
        return json.dumps(data).encode("utf-8")


class OpDocument(OpItem):
    def __init__(self, data: dict, contents: bytes):
        super().__init__(data)
        if self.category != "DOCUMENT":
            raise TypeError(f"This item is of type {self.type}, not DOCUMENT")
        self.contents = contents

    @classmethod
    def from_item(cls, item: OpItem, contents: bytes) -> "OpDocument":
        return cls(data=item._data, contents=contents)

    @property
    def filename(self):
        return self._data["files"][0]["name"]
