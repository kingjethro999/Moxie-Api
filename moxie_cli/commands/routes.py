import importlib

import click


@click.command()
@click.argument("app_path")
def routes(app_path: str) -> None:
    """Print all registered routes for a Moxie app."""
    try:
        module_str, app_str = app_path.split(":")
        module = importlib.import_module(module_str)
        app = getattr(module, app_str)
    except Exception as e:
        click.echo(f"Error loading app '{app_path}': {e}", err=True)
        return

    from moxie import Moxie
    if not isinstance(app, Moxie):
        click.echo(f"Object '{app_str}' is not a Moxie application.", err=True)
        return

    # Print header
    click.echo(f"{'METHOD':<8} {'PATH':<30} {'NAME':<20} {'TAGS'}")
    click.echo("-" * 70)

    for route in app.router.routes:
        methods = ",".join(route.methods)
        tags = ",".join(route.tags)
        click.echo(f"{methods:<8} {route.path:<30} {route.name:<20} {tags}")
