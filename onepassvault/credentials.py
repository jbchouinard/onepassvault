import os
from typing import Tuple

import hvac

from onepassvault.opw import OnePassword, OpItem, OpItemFieldType
from onepassvault.opw.client import OpItemNotFound
from onepassvault.userio import echo, input_bool
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
    print(item.to_json())
    config_data = {f: item.get_field_value(f) for f in VAULT_CONFIG_FIELDS}
    print(config_data)
    return VaultClientConfig.model_validate(config_data)


def get_vault_config(op: OnePassword) -> VaultClientConfig:
    if VAULT_CONFIG_OP_ITEM_ID:
        op_item_id = VAULT_CONFIG_OP_ITEM_ID
    else:
        op_item_id = input(
            "Use 1Password item for Vault credentials storage [blank to skip]: "
        ).strip()
        if op_item_id:
            echo(f'  To skip prompt next time:  export VAULT_CONFIG_OP_ITEM_ID="{op_item_id}"')
        else:
            echo("  To skip prompt next time:  export VAULT_CONFIG_OP_ITEM_ID=disable")

    if op_item_id and op_item_id != "disable":
        try:
            item = op.get_item(VAULT_CONFIG_OP_ITEM_ID)
            return op_item_to_vault_config(item)
        except OpItemNotFound:
            echo(f"The item {op_item_id} does not appear to exist in this account")

    vault_config = load_config()
    if op_item_id and op_item_id != "disable":
        save = input_bool(
            f"Save this Vault configuration to the 1Password item {op_item_id}?", False
        )
        if save:
            op_item = vault_config_to_op_item(vault_config, op_item_id)
            op.create_item(op_item)

    return vault_config


def start() -> Tuple[OnePassword, hvac.Client]:
    op = OnePassword()
    op.signin()
    echo(f"Signed in to 1Password account {op.account['email']}", 1)
    vault_config = get_vault_config(op)
    print(vault_config)
    vault_client = open_vault(vault_config)
    echo(f"Opened vault at {vault_config.url}", 1)
    return op, vault_client
