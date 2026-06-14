"""Slack alerting helper (offline-first). Logs when no webhook is configured."""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


def send_slack_alert(message: str, webhook_url: str | None = None) -> bool:
    url = webhook_url or os.getenv("SLACK_WEBHOOK_URL", "")
    if not url:
        logger.warning("[slack-disabled] %s", message)
        return False

    import httpx

    resp = httpx.post(url, json={"text": message}, timeout=10.0)
    resp.raise_for_status()
    return True
