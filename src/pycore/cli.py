"""CLI scaffolding with automatic task discovery."""

from __future__ import annotations

import importlib
import pkgutil
from typing import Any

import typer


def create_app(name: str, *, tasks_package: str = "tasks") -> typer.Typer:
    """Create a Typer app that auto-discovers task modules.

    Scans `tasks_package` for modules containing a Typer `app` and registers
    them as sub-commands.

    Usage in __main__.py:
        from pycore.cli import create_app
        app = create_app("msgflow", tasks_package="tasks")
        app()
    """
    root = typer.Typer(name=name, no_args_is_help=True)

    try:
        package = importlib.import_module(tasks_package)
    except ImportError:
        return root

    package_path = getattr(package, "__path__", None)
    if not package_path:
        return root

    for _, module_name, _ in pkgutil.iter_modules(package_path):
        module = importlib.import_module(f"{tasks_package}.{module_name}")
        # If module has a typer app, add it as a command group
        module_app: Any = getattr(module, "app", None)
        if isinstance(module_app, typer.Typer):
            root.add_typer(module_app, name=module_name)
        # If module has a single command function decorated with @app.command
        # registered via a module-level Typer, commands are already in module_app
        # Also support a bare `run` function as a simple command
        run_fn = getattr(module, "run", None)
        if run_fn and callable(run_fn) and not module_app:
            root.command(name=module_name)(run_fn)

    return root
