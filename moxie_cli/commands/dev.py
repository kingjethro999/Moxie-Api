import subprocess
import sys

import click


@click.command()
@click.argument("app_path")
@click.option("--host", default="127.0.0.1", help="Bind socket to this host.")
@click.option("--port", default=8000, help="Bind socket to this port.")
@click.option("--reload/--no-reload", default=True, help="Enable auto-reload.")
def dev(app_path: str, host: str, port: int, reload: bool) -> None:
    """Start the Moxie development server."""
    click.echo(f"Starting Moxie dev server for {app_path}...")
    
    cmd = [
        sys.executable, "-m", "uvicorn",
        app_path,
        "--host", host,
        "--port", str(port)
    ]
    if reload:
        cmd.append("--reload")
        
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        click.echo("\nStopping Moxie dev server...")
