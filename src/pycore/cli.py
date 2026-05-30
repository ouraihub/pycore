"""CLI scaffolding with automatic task discovery."""

from __future__ import annotations

import importlib
import pkgutil
from typing import Any

import typer

from pycore.callback import callback as callback_cmd


def create_app(name: str, *, tasks_package: str = "tasks") -> typer.Typer:
    """Create a Typer app that auto-discovers task modules.

    Auto-registers:
    - `callback` command (POST results.json to Worker)
    - All modules in `tasks_package` as sub-commands

    Usage in __main__.py:
        from pycore.cli import create_app
        app = create_app("myproject", tasks_package="tasks")
        app()
    """
    root = typer.Typer(name=name, no_args_is_help=True)
    root.command("callback")(callback_cmd)

    try:
        package = importlib.import_module(tasks_package)
    except ImportError:
        return root

    package_path = getattr(package, "__path__", None)
    if not package_path:
        return root

    for _, module_name, _ in pkgutil.iter_modules(package_path):
        module = importlib.import_module(f"{tasks_package}.{module_name}")
        module_app: Any = getattr(module, "app", None)
        if isinstance(module_app, typer.Typer):
            root.add_typer(module_app, name=module_name)
        run_fn = getattr(module, "run", None)
        if run_fn and callable(run_fn) and not module_app:
            root.command(name=module_name)(run_fn)

    return root
