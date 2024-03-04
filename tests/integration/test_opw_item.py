from onepassvault.opw import OnePassword, OpItem, OpItemFieldType


def test_item_crud(op: OnePassword, test_vault):
    new_item: OpItem = op.create_item_from_template("test-item", "Secure Note", vault=test_vault)
    assert new_item.vault.id == test_vault.id
    new_item.add_field("secret", OpItemFieldType.PASSWORD, "my-secret-password")
    new_item = op.update_item(new_item)

    assert len(op.get_items(vault=test_vault)) == 1

    op.delete_item(new_item)
    assert len(op.get_items(vault=test_vault)) == 0
