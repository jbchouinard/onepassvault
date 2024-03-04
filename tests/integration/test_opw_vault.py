import pytest
from .conftest import random_vault_id
from onepassvault.opw import OpVaultNotFound


def test_vault_create_delete(op):
    vault_name = random_vault_id()
    vault_created = op.create_vault(vault_name)
    assert vault_created.name == vault_name

    vault_got = op.get_vault(vault_name)
    assert vault_got.id == vault_created.id
    assert vault_got.name == vault_created.name
    assert vault_got.items == 0

    op.delete_vault(vault_created)
    with pytest.raises(OpVaultNotFound):
        op.get_vault(vault_name)
