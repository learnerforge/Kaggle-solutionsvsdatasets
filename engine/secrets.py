"""Kaggle credential resolution — security rule R12.

Order of precedence (first hit wins):

1. ``KAGGLE_USERNAME`` + ``KAGGLE_KEY`` environment variables
   (how GitHub Actions secrets and ``.env`` reach the CLI).
2. ``~/.kaggle/kaggle.json`` — the standard Kaggle CLI location.
3. ``ENGINE_KAGGLE_SOURCE=remote`` — fetch over HTTPS from a private endpoint.
   Disabled by default. If a future Vercel database is used, the *credentials*
   should still live in Vercel Environment Variables behind a tiny serverless
   endpoint, never as rows in a shared database: a database dump would leak
   the Kaggle account, while env vars are encrypted at rest and scoped.

The key is never printed, logged, or included in synced payloads. ``repr`` of
a resolved credential object is redacted.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from .settings import Settings


class CredentialError(RuntimeError):
    """No usable Kaggle credentials found."""


@dataclass(frozen=True)
class KaggleCredentials:
    username: str
    key: str
    source: str  # "env" | "kaggle.json" | "remote:<host>"

    def __repr__(self) -> str:  # R12: never leak the key via logs or errors
        return f"KaggleCredentials(username={self.username!r}, key='***', source={self.source!r})"

    __str__ = __repr__


def _from_env() -> KaggleCredentials | None:
    user = os.environ.get("KAGGLE_USERNAME")
    key = os.environ.get("KAGGLE_KEY")
    if user and key:
        return KaggleCredentials(user, key, "env")


def _from_kaggle_json() -> KaggleCredentials | None:
    path = Path.home() / ".kaggle" / "kaggle.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        user, key = data.get("username"), data.get("key")
        if user and key:
            return KaggleCredentials(user, key, "kaggle.json")
    except (OSError, ValueError):
        return None
    return None


def oauth_login_present() -> bool:
    """True when the Kaggle CLI 2.x has its own OAuth login on disk.

    `kaggle auth login` writes ``~/.kaggle/credentials.json`` (access/refresh
    tokens, expirations) which the CLI manages — including refresh. The engine
    deliberately does NOT parse or transport those tokens: it only recognises
    that a login exists so `auth_ready`/the dashboard report the truth, and the
    CLI self-authenticates in every subprocess.
    """
    path = Path.home() / ".kaggle" / "credentials.json"
    if not path.is_file():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return bool(isinstance(data, dict) and data.get("username") and data.get("access_token"))


def _from_remote(settings: Settings) -> KaggleCredentials | None:
    if not settings.kaggle_remote_url:
        return None
    import requests  # imported lazily: only needed in remote mode

    headers = {}
    if settings.kaggle_remote_token:
        headers["Authorization"] = f"Bearer {settings.kaggle_remote_token}"
    resp = requests.get(settings.kaggle_remote_url, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    user, key = data.get("username"), data.get("key")
    if user and key:
        from urllib.parse import urlparse

        host = urlparse(settings.kaggle_remote_url).netloc
        return KaggleCredentials(user, key, f"remote:{host}")
    return None


def resolve(settings: Settings | None = None) -> KaggleCredentials:
    """Resolve Kaggle credentials or raise :class:`CredentialError`."""
    settings = settings or __import__("engine.settings", fromlist=["load"]).load()
    creds = _from_env() or _from_kaggle_json()
    if creds is None and settings.kaggle_source == "remote":
        creds = _from_remote(settings)
    if creds is None:
        raise CredentialError(
            "No Kaggle credentials found. Either:\n"
            "  * set KAGGLE_USERNAME and KAGGLE_KEY (e.g. in .env — see .env.example), or\n"
            "  * run `kaggle auth login` (writes ~/.kaggle/kaggle.json), or\n"
            "  * for a managed setup, set ENGINE_KAGGLE_SOURCE=remote plus "
            "ENGINE_KAGGLE_REMOTE_URL (credentials served from Vercel env vars)."
        )
    return creds


def kaggle_env(settings: Settings | None = None) -> dict[str, str]:
    """A copy of ``os.environ`` with Kaggle credentials injected for the CLI.

    The kaggle CLI reads ``KAGGLE_USERNAME``/``KAGGLE_KEY`` directly, so this
    is all the wiring the subprocesses need — no kaggle.json file is written.
    """
    env = dict(os.environ)
    try:
        creds = resolve(settings)
    except CredentialError:
        return env  # let the CLI produce its own (equally informative) error
    env["KAGGLE_USERNAME"] = creds.username
    env["KAGGLE_KEY"] = creds.key
    return env


def auth_ready(settings: Settings | None = None) -> bool:
    """True if the Kaggle CLI can authenticate one way or another."""
    try:
        resolve(settings)
        return True
    except CredentialError:
        return oauth_login_present()
