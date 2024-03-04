import click
import sys

from onepassvault.opw import OnePassword


@click.command()
def cli():
    try:
        op = OnePassword("my.1password.com")
        op.delete_item(op.get_item("My First Test Item"))
        # vault = op.get_or_create_vault("TestVault-123")
        # op.set_default_vault(vault)
        # new_item = op.create_item_from_template("My First Test Item", "Secure Note")
        # print(new_item.to_json())
        # new_item.add_field("password", OpItemFieldType.PASSWORD, "my-secret-password")
        # item = op.create_item(new_item)
        # print(item.to_json())

    except Exception as e:
        click.echo(click.style(str(e), fg="red", bold=True))
        sys.exit(1)


if __name__ == "__main__":
    cli()
