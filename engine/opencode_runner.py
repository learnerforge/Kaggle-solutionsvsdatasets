"""Trigger OpenCode headlessly and capture the conversation.

This is the "the coder codes every single time it is triggered" half of the
engine. Invocation:

    opencode run --format json --auto [--standalone] [--model M] [--agent A] \\
                 --title "..." --file <prompt.md> "<short message>"

Notes that matter in practice:

* The prompt is attached with ``--file`` and the message stays short, because a
  Windows command line is limited to ~8k characters.
* ``--auto`` auto-approves permissions that are not explicitly denied, which is
  what makes unattended cycles possible (GitHub Actions).
* ``--standalone`` runs a private server — more reliable in CI than attaching to
  a background service.
* Output parsing is defensive: the CLI's JSON event schema is not contractual,
  so the runner extracts the longest plausible assistant text and always keeps
  the raw transcript on disk.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .settings import Settings, load


@dataclass
class OpenCodeResult:
    ok: bool
    returncode: int | None
    text: str
    session_id: str | None
    log_path: Path | None
    prompt_path: Path | None
    duration_sec: float
    error: str | None = None


def resolve_command() -> list[str]:
    found = shutil.which("opencode")
    if found:
        return [found]
    if shutil.os.name == "nt":  # pragma: no cover - PATH dependent
        return ["cmd", "/c", "opencode"]
    return ["opencode"]  # pragma: no cover


def available() -> bool:
    return shutil.which("opencode") is not None


def _extract_text(raw: str) -> tuple[str, str | None]:
    """Pull (assistant_text, session_id) out of the CLI output.

    Handles three shapes: a single JSON document, one JSON object per line
    (event stream), or plain text. Falls back to raw output.
    """
    texts: list[str] = []
    session_id: str | None = None

    def walk(node: object) -> None:
        nonlocal session_id
        if isinstance(node, dict):
            for key, value in node.items():
                low = key.lower()
                if isinstance(value, str) and value.strip():
                    if low in {"text", "content", "output", "response", "message"}:
                        texts.append(value)
                    if low in {"sessionid", "session_id"}:
                        session_id = session_id or value
                else:
                    walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    for chunk in (raw.splitlines() or [raw]):
        chunk = chunk.strip()
        if not chunk:
            continue
        try:
            walk(json.loads(chunk))
        except ValueError:
            if len(chunk) > 0:
                texts.append(chunk)

    if texts:
        text = max(texts, key=len)
        return text, session_id
    return raw.strip(), session_id


def run(
    message: str,
    *,
    slug: str,
    attempt: int = 1,
    prompt_path: Path | None = None,
    settings: Settings | None = None,
    title: str | None = None,
    timeout: int | None = None,
) -> OpenCodeResult:
    """Run one OpenCode turn and persist the transcript under train/logs/."""
    settings = settings or load()
    timeout = timeout or settings.opencode_timeout
    log_dir = settings.train_dir(slug) / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log_path = log_dir / f"opencode_attempt{attempt}_{stamp}.log"

    cmd = resolve_command() + ["run", "--format", "json", "--auto"]
    if settings.opencode_standalone:
        cmd.append("--standalone")
    if settings.opencode_model:
        cmd += ["--model", settings.opencode_model]
    if settings.opencode_agent:
        cmd += ["--agent", settings.opencode_agent]
    if title:
        cmd += ["--title", title]
    if prompt_path is not None:
        cmd += ["--file", str(prompt_path)]
    cmd.append(message)

    started = time.time()
    if not available() and not shutil.which("opencode"):
        error = ("opencode CLI not found on PATH. Install it (npm i -g opencode-ai) or "
                 "run the engine with --dry-run to inspect prompts without invoking the coder.")
        log_path.write_text(f"# opencode unavailable\n{error}\n", encoding="utf-8")
        return OpenCodeResult(False, None, "", None, log_path, prompt_path, 0.0, error)

    try:
        proc = subprocess.run(
            cmd, cwd=str(settings.repo_root), capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=timeout, env=dict(os.environ),
        )
        duration = time.time() - started
        text, session_id = _extract_text(proc.stdout or "")
        log_path.write_text(
            "# opencode transcript\n"
            f"# slug={slug} attempt={attempt} returncode={proc.returncode} duration={duration:.1f}s\n"
            f"# prompt={prompt_path}\n\n"
            f"----- PROMPT -----\n{_read(prompt_path)}\n\n"
            f"----- STDOUT -----\n{proc.stdout or ''}\n\n"
            f"----- STDERR -----\n{proc.stderr or ''}\n",
            encoding="utf-8",
        )
        ok = proc.returncode == 0 and bool(text.strip())
        error = None if ok else (proc.stderr or "").strip()[:2000] or "empty response"
        return OpenCodeResult(ok, proc.returncode, text, session_id, log_path,
                              prompt_path, duration, error)
    except subprocess.TimeoutExpired:
        duration = time.time() - started
        error = f"opencode exceeded ENGINE_OPENCODE_TIMEOUT ({timeout}s)"
        log_path.write_text(
            f"# opencode timeout after {duration:.0f}s\n# prompt={prompt_path}\n\n{_read(prompt_path)}",
            encoding="utf-8",
        )
        return OpenCodeResult(False, None, "", None, log_path, prompt_path, duration, error)
    except OSError as exc:  # pragma: no cover - platform dependent
        return OpenCodeResult(False, None, "", None, log_path, prompt_path,
                              time.time() - started, f"failed to launch opencode: {exc}")


def _read(path: Path | None) -> str:
    if path is None or not path.is_file():
        return "(no prompt file)"
    return path.read_text(encoding="utf-8")
