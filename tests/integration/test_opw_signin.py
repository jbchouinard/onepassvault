from onepassvault.opw import OnePassword


def test_op_signin_signout(op, test_account_url, test_account_email):
    op = OnePassword(test_account_url)
    assert op.account_url == test_account_url
    assert op.account is None
    assert test_account_url
    op.signin()
    assert op.account["email"] == test_account_email
    op.signout()
    assert op.account is None
