"""Built-in callback command — POST results.json to a Worker endpoint."""

from __future__ import annotations

import json
import os
from pathlib import Path

import typer

from pycore.http import post, HttpError
from pycore.log import logger

log = logger("callback")


def callback(
    file: Path = typer.Option(..., "--file", help="Path to results.json"),
):
    """Read results.json and POST to callback endpoint."""
    url = os.environ.get("CALLBACK_URL", "")
    secret = os.environ.get("CALLBACK_SECRET", "")
    if not url:
        typer.echo("Error: CALLBACK_URL not set", err=True)
        raise typer.Exit(1)

    if not file.exists():
        typer.echo(f"Error: {file} not found", err=True)
        raise typer.Exit(1)

    results = json.loads(file.read_text(encoding="utf-8"))
    payload = {"secret": secret, "action": "batch_result", "data": {"results": results}}
    log.info("Callback start", url=url, result_count=len(results))

    try:
        resp = post(url, json=payload, timeout=30)
        typer.echo(resp.body)
        log.info("Callback success", status=resp.status)
    except HttpError as e:
        log.error("Callback failed", status=e.status, error=e.body[:100])
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)
