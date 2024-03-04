import os
from pathlib import Path
from typing import Any, Optional

import hvac
from pydantic import BaseModel

from onepassvault.func import opt_int, opt_path, opt_str
from onepassvault.userio import input_str


class VaultError(RuntimeError):
    pass


VAULT_ENV_VARS = {
    "url": "VAULT_ADDR",
    "token": "VAULT_TOKEN",
    "namespace": "VAULT_NAMESPACE",
    "client_cert_path": "VAULT_CLIENT_CERT",
    "client_cert_key_path": "VAULT_CLIENT_KEY",
    "server_cert_path": "VAULT_CACERT",
    "timeout": "VAULT_TIMEOUT",
}


VAULT_CONFIG_FIELDS = list(VAULT_ENV_VARS.keys())


_vault_config_field_types = {
    "url": opt_str,
    "token": opt_str,
    "namespace": opt_str,
    "client_cert_path": opt_path,
    "client_cert_key_path": opt_path,
    "server_cert_path": opt_path,
    "timeout": opt_int,
}


class VaultClientConfig(BaseModel):
    url: Optional[str] = None
    token: Optional[str] = None
    namespace: Optional[str] = None
    client_cert_path: Optional[Path] = None
    client_cert_key_path: Optional[Path] = None
    server_cert_path: Optional[Path] = None
    timeout: Optional[int] = None

    def _from_env(self, attr: str, _):
        return self.cast_field(attr, os.getenv(VAULT_ENV_VARS[attr]))

    def _from_input(self, attr: str, current):
        default = opt_str(current) or ""
        return self.cast_field(attr, input_str(f"{VAULT_ENV_VARS[attr]}", default) or None)

    def _load(self, method, overwrite=False):
        for attr in VAULT_CONFIG_FIELDS:
            current = getattr(self, attr)
            if overwrite or current is None:
                new = method(attr, current)
                if new:
                    setattr(self, attr, new)

    @staticmethod
    def cast_field(attr: str, value: Any) -> Any:
        return _vault_config_field_types[attr](value)

    def load_env(self, overwrite=False):
        self._load(self._from_env, overwrite=overwrite)

    def load_interactive(self, overwrite=True):
        self._load(self._from_input, overwrite=overwrite)


DEFAULT_URL = "http://localhost:8200"
DEFAULT_TIMEOUT = 30


def load_config() -> VaultClientConfig:
    conf = VaultClientConfig()
    conf.load_env()
    conf.url = conf.url or DEFAULT_URL
    conf.timeout = conf.timeout or DEFAULT_TIMEOUT
    conf.load_interactive()
    return conf


def open_vault(config: Optional[VaultClientConfig] = None) -> hvac.Client:
    config = config or load_config()
    cert = None
    if config.client_cert_path and config.client_cert_key_path:
        cert = (str(config.client_cert_path), str(config.client_cert_key_path))

    client = hvac.Client(
        url=config.url,
        token=config.token,
        namespace=config.namespace,
        cert=cert,
        verify=config.server_cert_path,
        timeout=config.timeout,
    )
    return client


def assert_vault_is_live(client: hvac.Client):
    if not client.is_authenticated():
        raise VaultError("Vault client is not authenticated")
    if not client.sys.is_initialized():
        raise VaultError(f"Vault at {client.url} is not initialized")
    if client.sys.is_sealed():
        raise VaultError(f"Vault at {client.url} is sealed")
