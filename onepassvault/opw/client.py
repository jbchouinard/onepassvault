import copy
import json
import os
import re
import shutil
from subprocess import PIPE, Popen
from typing import List, Optional, Set, Tuple, Union

from .schema import OpDocument, OpItem, OpVault


def resolve_exe_path(executable: str) -> str:
    if os.path.sep in executable:
        return os.path.abspath(executable)
    else:
        return shutil.which(executable)


RE_OP_ERROR = re.compile(r"\[ERROR\] \d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2} (?P<message>.*)")


class OpProcessError(Exception):
    def __init__(self, return_code, message):
        self.return_code = return_code
        self.message = message

    def __str__(self) -> str:
        return str(self.message)


class OpNotSignedIn(OpProcessError):
    pass


class OpVaultNotFound(OpProcessError):
    pass


class OpItemNotFound(OpProcessError):
    pass


ERROR_MATCH = {
    "not signed in": OpNotSignedIn,
    "isn't a vault": OpVaultNotFound,
    "isn't an item": OpItemNotFound,
}


def op_exception(return_code: int, stderr: bytes) -> OpProcessError:
    m = RE_OP_ERROR.match(stderr.decode("utf-8", errors="ignore"))
    if m:
        message = m.group("message")
    else:
        message = stderr

    for msg_fragment, exc_type in ERROR_MATCH.items():
        if msg_fragment in message:
            return exc_type(return_code, message)
    return OpProcessError(return_code, message)


VaultOrStr = Union[OpVault, str]


class OnePassword:
    "OnePassword is a Python wrapper around the 1Password CLI tool."

    def __init__(
        self,
        account_url: Optional[str] = None,
        op_executable: str = "op",
        subprocess_timeout: int = 30,
    ):
        self.op_exe = resolve_exe_path(op_executable)
        self.timeout = float(subprocess_timeout)
        self.account_url = account_url
        self.account = None
        self.default_vault = None
        self._valid_template_names = None
        self._templates = {}

    def call(self, args, in_bytes: Optional[bytes] = None, json_format=True):
        if in_bytes is not None:
            stdin = PIPE
        else:
            stdin = None

        cmd = [self.op_exe] + list(args)
        if json_format:
            cmd += ["--format", "json"]
        if self.account_url:
            cmd += ["--account", self.account_url]

        p = Popen(cmd, stdout=PIPE, stderr=PIPE, stdin=stdin)
        out_data, err_data = p.communicate(in_bytes, timeout=self.timeout)

        if p.returncode != 0:
            raise op_exception(p.returncode, err_data)
        elif json_format:
            if out_data:
                return json.loads(out_data)
            else:
                return None
        else:
            return out_data

    def _get_vault_id_or_name(self, vault: Optional[VaultOrStr]) -> Optional[str]:
        if vault is None:
            return None
        elif isinstance(vault, str):
            return vault
        else:
            return vault.id

    def _with_vault(self, args, vault: Optional[VaultOrStr]) -> List[str]:
        vault_id = self._get_vault_id_or_name(vault or self.default_vault)
        if vault_id:
            args.extend(["--vault", vault_id])
        return args

    def whoami(self):
        return self.call(["whoami"])

    def signin(self):
        cmd = ["signin"]
        self.call(cmd)
        self.account = self.whoami()
        self.account_url = self.account["url"]

    def signout(self):
        self.call(["signout"])
        self.account = None

    def get_item(self, item_id_or_name: str, vault: Optional[VaultOrStr] = None) -> OpItem:
        return OpItem(self.call(self._with_vault(["item", "get", item_id_or_name], vault)))

    def get_items(self, vault: Optional[VaultOrStr] = None) -> List[OpItem]:
        items = self.call(self._with_vault(["item", "list"], vault))
        return [OpItem(item) for item in items]

    def create_item(self, item: OpItem, vault: Optional[VaultOrStr] = None) -> OpItem:
        if item.id:
            raise ValueError("Cannot create item with an id, use update_item")
        created = self.call(
            self._with_vault(["item", "create", "-"], vault), in_bytes=item.to_json()
        )
        return OpItem(created)

    def create_item_from_template(
        self, title: str, template_name: str, vault: Optional[VaultOrStr] = None
    ) -> OpItem:
        tmpl = self._get_template(template_name)
        tmpl["title"] = title
        return self.create_item(OpItem(tmpl), vault=vault)

    def update_item(self, item: OpItem) -> OpItem:
        item_id = item.id
        vault_id = item.vault.id
        assert item_id and vault_id
        updated = self.call(
            self._with_vault(["item", "edit", item_id], vault=vault_id), in_bytes=item.to_json()
        )
        return OpItem(updated)

    def delete_item(self, item: OpItem):
        item_id = item.id
        vault_id = item.vault.id
        assert item_id and vault_id
        self.call(self._with_vault(["item", "delete", item_id], vault=vault_id))

    def get_document(
        self, item_id_or_name: str, vault: Optional[VaultOrStr] = None
    ) -> Tuple[OpDocument, bytes]:
        item = self.get_item(item_id_or_name)
        contents = self.call(
            self._with_vault(["document", "get", "--force", item_id_or_name], vault),
            json_format=False,
        )
        return OpDocument.from_item(item, contents)

    def create_document(
        self,
        filename: str,
        contents: bytes,
        title: Optional[str] = None,
        vault: Optional[VaultOrStr] = None,
    ) -> OpDocument:
        cmd = ["document", "create", "-", "--file-name", filename]
        if title:
            cmd += ["--title", title]

        doc_uuid = self.call(self._with_vault(cmd, vault), in_bytes=contents)["uuid"]
        item = self.get_item(doc_uuid)
        return OpDocument.from_item(item, contents)

    def update_document(
        self,
        document: OpDocument,
        contents: bytes,
        filename: Optional[str] = None,
        title: Optional[str] = None,
    ) -> OpDocument:
        cmd = ["document", "edit", document.id, "-"]
        if filename:
            cmd += ["--file-name", filename]
        if title:
            cmd += ["--title", title]
        self.call(cmd, in_bytes=contents)
        updated_item = self.update_item(document)
        return OpDocument.from_item(updated_item, contents)

    def delete_document(self, document: OpDocument):
        self.delete_item(document)

    def get_vault(self, vault: VaultOrStr) -> OpVault:
        data = self.call(["vault", "get", self._get_vault_id_or_name(vault)])
        return OpVault.model_validate(data)

    def create_vault(self, name: str) -> OpVault:
        return OpVault.model_validate(self.call(["vault", "create", name]))

    def get_or_create_vault(self, name: str):
        try:
            vault = self.get_vault(name)
        except OpVaultNotFound:
            vault = self.create_vault(name)
        return vault

    def delete_vault(self, vault: VaultOrStr):
        vault_id = self._get_vault_id_or_name(vault)
        vault = self.get_vault(vault_id)  # Get up to date item count

        if vault.items > 0:
            raise ValueError(f"{vault} is not empty, this tool will not delete it")

        self.call(["vault", "delete", vault_id])

    def set_default_vault(self, vault: VaultOrStr):
        self.default_vault = vault

    @property
    def valid_template_names(self) -> Set[str]:
        if self._valid_template_names is None:
            self._valid_template_names = self._get_template_names()
        return set(self._valid_template_names)

    def _get_template_names(self) -> Set[str]:
        templates = self.call(["item", "template", "list"])
        return {t["name"] for t in templates}

    def _get_template(self, name: str) -> dict:
        if name not in self.valid_template_names:
            raise ValueError(
                f"{name} is one of the valid templates: {', '.join(self.valid_template_names)}"
            )
        if name not in self._templates:
            self._templates[name] = self.call(["item", "template", "get", name])
        return copy.deepcopy(self._templates[name])
