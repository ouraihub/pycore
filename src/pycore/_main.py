"""pycore CLI — project scaffolding tool."""

from pathlib import Path
from typing import Optional

import typer

from pycore.init import init_project

app = typer.Typer(name="pycore", no_args_is_help=True)


@app.command()
def init(
    name: str = typer.Argument(..., help="Project name"),
    directory: Optional[Path] = typer.Option(None, "--dir", help="Target directory (default: ./<name>)"),
):
    """Create a new pycore-based project."""
    root = init_project(name, directory)
    typer.echo(f"✅ Created project: {root}")
    typer.echo(f"\n  cd {root.name}")
    typer.echo("  uv sync")
    typer.echo(f"  uv run python -m {name} --help")


if __name__ == "__main__":
    app()
