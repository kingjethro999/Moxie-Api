import sys
import click
from moxie_cli.commands.dev import dev
from moxie_cli.commands.routes import routes
from moxie_cli.commands.openapi import openapi

@click.group()
def main() -> None:
    """Moxie CLI — the ultimate tool for Moxie developers."""
    pass

main.add_command(dev)
main.add_command(routes)
main.add_command(openapi)

if __name__ == "__main__":
    main()
