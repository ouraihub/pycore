"""Notification sender — Telegram / Feishu, auto-selected by env."""

from __future__ import annotations

import os

from pycore.http import HttpError, post
from pycore.log import logger

log = logger("notify")


def notify(message: str, *, channel: str | None = None) -> bool:
    """Send a notification. Channel auto-detected from env if not specified."""
    channel = channel or os.environ.get("NOTIFY_CHANNEL", "")

    if channel == "telegram":
        return _send_telegram(message)
    elif channel == "feishu":
        return _send_feishu(message)
    else:
        log.warning("No notify channel configured", channel=channel)
        return False


def _send_telegram(message: str) -> bool:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        log.error("TELEGRAM_BOT_TOKEN/CHAT_ID not set")
        return False
    try:
        post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"},
        )
        return True
    except HttpError as e:
        log.error("Telegram notify failed", status=e.status)
        return False


def _send_feishu(message: str) -> bool:
    webhook = os.environ.get("FEISHU_WEBHOOK_URL", "")
    if not webhook:
        log.error("FEISHU_WEBHOOK_URL not set")
        return False
    try:
        post(webhook, json={"msg_type": "text", "content": {"text": message}})
        return True
    except HttpError as e:
        log.error("Feishu notify failed", status=e.status)
        return False
