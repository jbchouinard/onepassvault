import os
from typing import Tuple

import hvac

from clickio.input import prompt, prompt_yn
from clickio.output import echo_info, echo_info_v
from onepassvault.opw import OnePassword, OpItem, OpItemFieldType
from onepassvault.opw.client import OpItemNotFound
from onepassvault.vault import (
    VAULT_CONFIG_FIELDS,
    VaultClientConfig,
    load_config,
    open_vault,
)

VAULT_CONFIG_OP_VAULT_ID = os.getenv("VAULT_CONFIG_OP_VAULT_ID")
VAULT_CONFIG_OP_ITEM_ID = os.getenv("VAULT_CONFIG_OP_ITEM_ID")


VAULT_CONFIG_FIELD_TYPES = {"token": OpItemFieldType.PASSWORD}


def vault_config_to_op_item(config: VaultClientConfig, name: str) -> OpItem:
    item = OpItem({"title": name, "category": "API_CREDENTIAL", "fields": []})
    for k, v in config.model_dump().items():
        if v is not None:
            item.add_field(
                name=k, type=VAULT_CONFIG_FIELD_TYPES.get(k, OpItemFieldType.TEXT), value=str(v)
            )
    return item


def op_item_to_vault_config(item: OpItem) -> VaultClientConfig:
    config_data = {f: item.get_field_value(f) for f in VAULT_CONFIG_FIELDS}
    return VaultClientConfig.model_validate(config_data)


def get_vault_config(op: OnePassword) -> VaultClientConfig:
    if VAULT_CONFIG_OP_ITEM_ID:
        op_item_id = VAULT_CONFIG_OP_ITEM_ID
    else:
        op_item_id = prompt("Use 1Password item for Vault credentials storage", "skip")
        echo_info(
            f"\n   To skip this prompt next time:  export VAULT_CONFIG_OP_ITEM_ID='{op_item_id}'\n",
        )

    if op_item_id and op_item_id != "skip":
        try:
            item = op.get_item(op_item_id)
            return op_item_to_vault_config(item)
        except OpItemNotFound:
            echo_info(f"The item {op_item_id} does not appear to exist in this account")

    echo_info("Enter your Vault credentials:")
    vault_config = load_config()
    if op_item_id and op_item_id != "skip":
        save = prompt_yn(
            f"Save this Vault configuration to the 1Password item {op_item_id}?", False
        )
        if save:
            op_item = vault_config_to_op_item(vault_config, op_item_id)
            op.create_item(op_item)

    return vault_config


def start() -> Tuple[OnePassword, hvac.Client]:
    op = OnePassword()
    op.signin()
    echo_info_v(f"Signed in to 1Password account {op.account['email']}")
    vault_config = get_vault_config(op)
    vault_client = open_vault(vault_config)
    echo_info_v(f"Using Vault at {vault_config.url}")
    return op, vault_client
