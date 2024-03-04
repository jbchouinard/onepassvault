import pytest
import os
from onepassvault.opw.client import OnePassword
from uuid import uuid4


@pytest.fixture(scope="session")
def test_account_url() -> str:
    return os.environ["OPV_TEST_ACCOUNT_URL"]


@pytest.fixture(scope="session")
def test_account_email() -> str:
    return os.environ["OPV_TEST_ACCOUNT_EMAIL"]


@pytest.fixture(scope="session")
def op(test_account_url, test_account_email) -> OnePassword:
    client = OnePassword(test_account_url)
    client.signin()
    if client.account["email"] != test_account_email:
        raise RuntimeError(
            f"1Password was signed in to {client.account['email']}, not the expected test account "
            f"{test_account_email}. You may have to manually sign in to the desired account before "
            "running the tests."
        )
    return client


def random_vault_id() -> str:
    return f"test-vault-{str(uuid4())}"


@pytest.fixture(scope="function")
def test_vault(op: OnePassword):
    vault = op.create_vault(random_vault_id())
    op.set_default_vault(vault)
    yield vault
    op.delete_vault(vault)
