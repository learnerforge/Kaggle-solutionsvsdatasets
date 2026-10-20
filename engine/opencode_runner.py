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
* The transcript is **streamed to disk line by line** while the process runs,
  so a timeout, a kill or a crash still leaves the full partial conversation
  for the next attempt to learn from. A heartbeat line is printed every 30s so
  long coder turns never look hung.
* Transient failures (non-zero exit, empty response) are retried once by
  default (``ENGINE_OPENCODE_RETRIES``); timeouts are never retried — they
  would only double the wall-clock cost of a genuinely slow turn.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import threading
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


def _invoke(cmd: list[str], *, timeout: int, log, label: str,
            cwd: Path) -> tuple[int | None, str, str | None, float, str | None, bool]:
    """Run one opencode process with a streamed transcript.

    Returns ``(returncode, text, session_id, duration, error, timed_out)``.
    On timeout the process is killed but everything already streamed to ``log``
    (and to the collected lines) is kept — partial transcripts are the whole
    point of streaming.
    """
    started = time.time()
    deadline = started + timeout
    log.write(f"----- TRY cmd: {' '.join(cmd)} -----\n")
    log.flush()

    try:
        proc = subprocess.Popen(
            cmd, cwd=str(cwd), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", errors="replace", env=dict(os.environ),
        )
    except OSError as exc:  # pragma: no cover - platform dependent
        return None, "", None, 0.0, f"failed to launch opencode: {exc}", False

    out_lines: list[str] = []
    err_lines: list[str] = []

    def drain(pipe, sink: list[str], prefix: str = "") -> None:
        try:
            for line in pipe:
                sink.append(line)
                log.write(prefix + line)
                log.flush()
        except (ValueError, OSError):  # pragma: no cover - pipe closed under us
            pass

    threads = [
        threading.Thread(target=drain, args=(proc.stdout, out_lines), daemon=True),
        threading.Thread(target=drain, args=(proc.stderr, err_lines, "[stderr] "), daemon=True),
    ]
    for thread in threads:
        thread.start()

    timed_out = False
    next_beat = started + 30
    while proc.poll() is None:
        now = time.time()
        if now >= deadline:
            timed_out = True
            proc.kill()
            break
        if now >= next_beat:
            print(f"[opencode] {label} running ({now - started:.0f}s / {timeout}s)",
                  file=sys.stderr, flush=True)
            next_beat = now + 30
        time.sleep(0.5)

    try:
        proc.wait(timeout=30)
    except subprocess.TimeoutExpired:  # pragma: no cover - defensive
        proc.kill()
    for thread in threads:
        thread.join(timeout=10)

    duration = time.time() - started
    text, session_id = _extract_text("".join(out_lines))
    returncode = proc.returncode

    if timed_out:
        error = (f"opencode exceeded ENGINE_OPENCODE_TIMEOUT ({timeout}s); "
                 "partial transcript kept")
    elif returncode != 0 or not text.strip():
        error = ("".join(err_lines).strip()[:2000]
                 or f"opencode exited {returncode} with an empty response")
    else:
        error = None
    return returncode, text, session_id, duration, error, timed_out


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

    if not available() and not shutil.which("opencode"):
        error = ("opencode CLI not found on PATH. Install it (npm i -g opencode-ai) or "
                 "run the engine with --dry-run to inspect prompts without invoking the coder.")
        log_path.write_text(f"# opencode unavailable\n{error}\n", encoding="utf-8")
        return OpenCodeResult(False, None, "", None, log_path, prompt_path, 0.0, error)

    tries = 1 + max(0, int(getattr(settings, "opencode_retries", 0)))
    label = f"{slug} attempt {attempt}"
    returncode: int | None = None
    text = ""
    session_id: str | None = None
    error: str | None = None
    timed_out = False
    total_duration = 0.0

    with log_path.open("w", encoding="utf-8") as log:
        log.write("# opencode transcript\n"
                  f"# slug={slug} attempt={attempt} prompt={prompt_path}\n\n"
                  f"----- PROMPT -----\n{_read(prompt_path)}\n\n")
        log.flush()
        for try_no in range(1, tries + 1):
            if try_no > 1:
                log.write(f"\n----- RETRY {try_no}/{tries} (previous: {error}) -----\n\n")
                log.flush()
                print(f"[opencode] {label}: retrying after failure — {error}",
                      file=sys.stderr, flush=True)
            (returncode, text, session_id, duration, error, timed_out) = _invoke(
                cmd, timeout=timeout, log=log, label=label, cwd=settings.repo_root,
            )
            total_duration += duration
            ok = returncode == 0 and bool(text.strip()) and not timed_out
            # Retry only transient failures; timeouts would cost the full
            # budget again, so they break out immediately.
            if ok or timed_out or try_no == tries:
                break

    ok = returncode == 0 and bool(text.strip()) and not timed_out
    if not ok and not timed_out and tries > 1:
        error = f"{error} (after {tries} tries)"
    return OpenCodeResult(ok, returncode, text, session_id, log_path,
                          prompt_path, total_duration, error)


def _read(path: Path | None) -> str:
    if path is None or not path.is_file():
        return "(no prompt file)"
    return path.read_text(encoding="utf-8")
