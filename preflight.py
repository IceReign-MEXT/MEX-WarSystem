"""Fail-fast configuration checks before importing the Telegram application.

This prevents main.py's import-time webhook route from crashing with an
opaque AttributeError when required deployment settings are absent.
"""
from __future__ import annotations

import os
import re
import runpy
import sys
from urllib.parse import urlparse

REQUIRED = ("BOT_TOKEN", "ADMIN_ID", "MASTER_WALLET", "WEBHOOK_URL", "WEBHOOK_SECRET", "DATABASE_URL")


def validate_environment(environ: dict[str, str] | None = None) -> list[str]:
    env = os.environ if environ is None else environ
    errors = [f"Missing required environment variable: {key}" for key in REQUIRED if not env.get(key, "").strip()]

    token = env.get("BOT_TOKEN", "").strip()
    if token and not re.fullmatch(r"\d+:[A-Za-z0-9_-]{20,}", token):
        errors.append("BOT_TOKEN does not have the expected Telegram bot-token format.")

    admin_id = env.get("ADMIN_ID", "").strip()
    if admin_id:
        try:
            if int(admin_id) <= 0:
                raise ValueError
        except ValueError:
            errors.append("ADMIN_ID must be a positive integer.")

    wallet = env.get("MASTER_WALLET", "").strip()
    if wallet and not re.fullmatch(r"[1-9A-HJ-NP-Za-km-z]{32,44}", wallet):
        errors.append("MASTER_WALLET does not look like a Solana public address.")

    database_url = env.get("DATABASE_URL", "").strip()\n    if database_url and not database_url.startswith(("postgres://", "postgresql://")):\n        errors.append("DATABASE_URL must be a PostgreSQL connection URL.")\n\n    webhook_secret = env.get("WEBHOOK_SECRET", "").strip()
    if webhook_secret and (len(webhook_secret) < 32 or len(webhook_secret) > 256 or not re.fullmatch(r"[A-Za-z0-9_-]+", webhook_secret)):
        errors.append("WEBHOOK_SECRET must be 32-256 characters using letters, numbers, underscores or hyphens.")

    webhook_url = env.get("WEBHOOK_URL", "").strip()
    if webhook_url:
        parsed = urlparse(webhook_url)
        if parsed.scheme != "https" or not parsed.netloc or parsed.path not in ("", "/"):
            errors.append("WEBHOOK_URL must be an HTTPS origin, without a path.")

    port = env.get("PORT", "10000").strip()
    try:
        if not 1 <= int(port) <= 65535:
            raise ValueError
    except ValueError:
        errors.append("PORT must be an integer between 1 and 65535.")

    return errors


def main() -> int:
    errors = validate_environment()
    if errors:
        for error in errors:
            print(f"CONFIGURATION ERROR: {error}", file=sys.stderr)
        return 1

    print("Configuration preflight passed; starting existing main.py.")
    runpy.run_path("main.py", run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
