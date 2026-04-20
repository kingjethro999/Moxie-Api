import click
import importlib
import json
import yaml

@click.group()
def openapi() -> None:
    """OpenAPI commands."""
    pass

@openapi.command()
@click.argument("app_path")
@click.option("--output", "-o", type=click.Path(), help="Output file path.")
@click.option("--format", "-f", type=click.Choice(["json", "yaml"]), default="json", help="Output format.")
def export(app_path: str, output: str, format: str) -> None:
    """Export OpenAPI specification to a file."""
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

    spec = app.openapi()
    
    if format == "json":
        content = json.dumps(spec, indent=2)
    else:
        content = yaml.dump(spec, sort_keys=False)

    if output:
        with open(output, "w") as f:
            f.write(content)
        click.echo(f"OpenAPI spec exported to {output}")
    else:
        click.echo(content)
