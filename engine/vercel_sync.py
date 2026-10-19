"""Optional sync with a Vercel-hosted database (non-secret data only).

Design decision (see the answer to "no Vercel DB yet"): the engine is built so
that a Vercel Postgres/KV database can be added later without touching the
pipeline. The contract is deliberately tiny:

* **push** — POST the dashboard projection (competitions, scores, checks,
  rulebook version) to ``VERCEL_SYNC_URL`` with `Authorization: Bearer
  $VERCEL_SYNC_TOKEN``. On the Vercel side a serverless function writes it to
  Postgres/KV.
* **pull** — GET the same URL with ``?action=queue`` to fetch a list of
  competition slugs to prioritise. Optional.

What is **never** synced: Kaggle credentials, local paths, dataset contents.
Kaggle credentials stay in Vercel *Environment Variables* (encrypted at rest,
scoped per deployment) and are served — if ever — by a dedicated endpoint that
the engine reads only when ``ENGINE_KAGGLE_SOURCE=remote`` (see
``engine/secrets.py``).
"""

from __future__ import annotations

import json

from .settings import Settings, load


def status(settings: Settings | None = None) -> dict:
    settings = settings or load()
    return {
        "enabled": bool(settings.vercel_sync_url),
        "url_configured": bool(settings.vercel_sync_url),
        "token_configured": bool(settings.vercel_sync_token),
        "syncs": "competition metadata, OOF/LB scores, requirement checks, rulebook version",
        "never_syncs": "Kaggle credentials, dataset contents, local file paths",
    }


def push(settings: Settings | None = None) -> dict:
    settings = settings or load()
    if not settings.vercel_sync_url:
        return {"enabled": False, "reason": "VERCEL_SYNC_URL is not set"}

    import requests

    from . import report

    payload = report.build_dashboard(settings)
    headers = {"Content-Type": "application/json"}
    if settings.vercel_sync_token:
        headers["Authorization"] = f"Bearer {settings.vercel_sync_token}"
    try:
        resp = requests.post(settings.vercel_sync_url, headers=headers,
                             data=json.dumps(payload), timeout=30)
    except Exception as exc:  # noqa: BLE001 - sync is best-effort, never fatal
        return {"enabled": True, "ok": False, "error": str(exc)}
    return {
        "enabled": True,
        "ok": resp.status_code < 400,
        "status_code": resp.status_code,
        "competitions": len(payload.get("competitions", [])),
        "detail": resp.text[:500],
    }


def pull(settings: Settings | None = None) -> dict:
    """Fetch a prioritised queue of competition slugs from the remote store."""
    settings = settings or load()
    if not settings.vercel_sync_url:
        return {"enabled": False, "queue": []}

    import requests

    headers = {}
    if settings.vercel_sync_token:
        headers["Authorization"] = f"Bearer {settings.vercel_sync_token}"
    try:
        resp = requests.get(settings.vercel_sync_url, headers=headers,
                            params={"action": "queue"}, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:  # noqa: BLE001
        return {"enabled": True, "ok": False, "error": str(exc), "queue": []}
    queue = data.get("queue") if isinstance(data, dict) else None
    return {"enabled": True, "ok": True,
            "queue": queue if isinstance(queue, list) else []}
