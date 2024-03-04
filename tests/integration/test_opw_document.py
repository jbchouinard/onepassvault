import pytest

from onepassvault.opw import OnePassword, OpItemNotFound


def test_document_crud(op: OnePassword, test_vault):
    contents = "this is a secret file!".encode("utf-8")
    new_doc = op.create_document("secrets.txt", contents, title="Secrets", vault=test_vault)
    assert new_doc.title == "Secrets"
    assert new_doc.filename == "secrets.txt"
    assert new_doc.contents == contents

    doc = op.get_document(new_doc.id)
    assert doc.contents == contents

    op.delete_document(doc)

    with pytest.raises(OpItemNotFound):
        op.get_document(new_doc.id)
