"""Thin, defensive wrapper over the Kaggle CLI (v2.x, `--format json`).

Everything shells out to the installed `kaggle` command rather than the old
`kaggle-api` python package, because the CLI is what the user already has
authenticated (Kaggle CLI 2.2.x: `kaggle auth login`).

All JSON parsing is best-effort: Kaggle has changed response shapes across
CLI versions, so every parser degrades to an empty result with a warning
instead of crashing the cycle.
"""

from __future__ import annotations

import csv
import io
import json
import re
import shutil
import subprocess
import zipfile
from pathlib import Path
from typing import Any

from . import secrets
from .settings import Settings, load


class KaggleCLIError(RuntimeError):
    def __init__(self, message: str, stderr: str = "", returncode: int | None = None):
        super().__init__(message)
        self.stderr = stderr
        self.returncode = returncode


def _cli_prefix() -> list[str]:
    """Resolve the kaggle executable for Windows (.cmd/.bat) and POSIX."""
    found = shutil.which("kaggle")
    if found:
        return [found]
    if shutil.os.name == "nt":  # pragma: no cover - depends on PATH
        return ["cmd", "/c", "kaggle"]
    return ["kaggle"]  # pragma: no cover


def to_slug(value: str | None) -> str:
    """Normalise a competition reference to a bare slug.

    The CLI returns `ref` as a full URL (https://www.kaggle.com/competitions/
    titanic) in list output but as a bare slug elsewhere. Anything reaching the
    pipeline must be a slug, or downloads 404.
    """
    if not value:
        return ""
    value = value.strip().rstrip("/")
    if "/" in value:
        value = value.split("/")[-1]
    return value


def cli_available() -> bool:
    return shutil.which("kaggle") is not None


def _try_json(text: str) -> Any | None:
    text = text.strip().lstrip("﻿")
    if not text:
        return None
    try:
        return json.loads(text)
    except ValueError:
        return None


class KaggleClient:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or load()
        self.env = secrets.kaggle_env(self.settings)

    # --- low level ----------------------------------------------------------

    def _run(self, args: list[str], timeout: int = 600) -> str:
        cmd = _cli_prefix() + args
        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True, encoding="utf-8",
                errors="replace", timeout=timeout, env=self.env,
            )
        except FileNotFoundError as exc:
            raise KaggleCLIError(
                "kaggle CLI not found. Install with `pip install kaggle` and run "
                "`kaggle auth login`."
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise KaggleCLIError(f"kaggle {' '.join(args[:3])} timed out after {timeout}s") from exc
        if proc.returncode != 0:
            err = (proc.stderr or proc.stdout or "").strip()
            hint = ""
            low = err.lower()
            if "403" in low or "forbidden" in low:
                hint = ("\nHint: join the competition in the browser and accept its rules; "
                        "the API token alone is not enough (per-competition rule acceptance).")
            elif "401" in low or "unauthorized" in low or "credentials" in low:
                hint = ("\nHint: credentials missing or expired. Run `kaggle auth login` or set "
                        "KAGGLE_USERNAME / KAGGLE_KEY (see engine/secrets.py).")
            raise KaggleCLIError(
                f"`kaggle {' '.join(args[:4])}` failed (exit {proc.returncode}): {err}{hint}",
                stderr=err, returncode=proc.returncode,
            )
        return proc.stdout or ""

    def _run_json(self, args: list[str], timeout: int = 600) -> Any | None:
        out = self._run(args + ["--format", "json"], timeout=timeout)
        return _try_json(out)

    # --- competition metadata -----------------------------------------------

    def list_competitions(self, search: str | None = None, category: str = "all",
                          page_size: int = 20) -> list[dict[str, Any]]:
        args = ["competitions", "list", "--category", category,
                "--sort-by", "recentlyCreated", "--page-size", str(page_size)]
        if search:
            args += ["--search", search]
        data = self._run_json(args) or []
        rows = data if isinstance(data, list) else []
        for row in rows:
            # `ref` is a full URL; expose a bare `slug` alongside for callers.
            row["slug"] = to_slug(row.get("ref") or row.get("slug"))
        return rows

    def files(self, slug: str) -> list[dict[str, Any]]:
        """Competition files. JSON shape: a plain list of {name, size, ...}.

        Older/newer CLI versions may wrap it in a dict with a nextPageToken;
        only then do we page — a plain list means "done" (re-fetching it would
        just duplicate entries forever).
        """
        files: list[dict[str, Any]] = []
        page_token: str | None = None
        for _ in range(50):  # hard stop against pathological paging
            args = ["competitions", "files", slug, "--page-size", "200"]
            if page_token:
                args += ["--page-token", page_token]
            data = self._run_json(args)
            if isinstance(data, list):
                files.extend(data)
                break
            if isinstance(data, dict):
                files.extend(data.get("files") or data.get("results") or [])
                page_token = data.get("nextPageToken") or data.get("next_page_token")
                if not page_token:
                    break
                continue
            break
        # De-duplicate by name defensively (mixed paging shapes across versions).
        deduped: dict[str, dict[str, Any]] = {}
        for item in files:
            deduped.setdefault(str(item.get("name") or item.get("ref") or id(item)), item)
        return list(deduped.values())

    def pages(self, slug: str) -> list[dict[str, Any]]:
        # NOTE: the CLI wants the competition positional in BOTH positions —
        # `pages <slug> list <slug>` — because the subparser overwrites the
        # parent's competition argument (argparse subparser default quirk).
        data = self._run_json(["competitions", "pages", slug, "list", slug]) or []
        if isinstance(data, list):
            return data
        return data.get("pages", []) if isinstance(data, dict) else []

    def pages_with_content(self, slug: str) -> list[dict[str, Any]]:
        """All competition pages with their full content, in one call."""
        data = self._run_json(
            ["competitions", "pages", slug, "list", slug, "--content"]
        ) or []
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data.get("pages", [])
        return []

    def page_content(self, slug: str, page_name: str) -> str:
        """Full content of one competition page (description/evaluation/rules)."""
        data = self._run_json(
            ["competitions", "pages", slug, "list", slug,
             "--content", "--page-name", page_name]
        )
        return _extract_text(data)

    def problem_statement(self, slug: str) -> str:
        """Problem statement + evaluation + rules text, markdown-ish.

        One `--content` call fetches every page; sections are assembled from
        whichever pages carry real content. Falls back to scraping the public
        overview page when the CLI cannot serve them (e.g. competitions the
        account has not joined).
        """
        sections: list[str] = []
        try:
            pages = self.pages_with_content(slug)
        except KaggleCLIError:
            pages = []
        # Read order: the challenge first, then how it is scored, then the
        # meta pages (the CLI returns them in its own arbitrary order).
        priority = ["description", "evaluation", "data-description", "rules"]
        ordered = sorted(
            enumerate(pages),
            key=lambda pair: (priority.index(str(pair[1].get("name", "")).lower())
                              if str(pair[1].get("name", "")).lower() in priority
                              else len(priority), pair[0]),
        )
        for _, page in ordered:
            name = str(page.get("name") or page.get("title") or "page")
            content = page.get("content")
            if isinstance(content, str) and content.strip():
                sections.append(f"## {name}\n\n{content.strip()}")
        if sections:
            return "\n\n".join(sections)
        return self._scrape_overview(slug)

    @staticmethod
    def _scrape_overview(slug: str) -> str:
        import requests

        url = f"https://www.kaggle.com/competitions/{slug}"
        try:
            resp = requests.get(url, timeout=30, headers={"User-Agent": "kaggle-solutions-engine"})
            resp.raise_for_status()
        except Exception as exc:  # noqa: BLE001 - degrade, never crash the cycle
            return f"(could not fetch {url}: {exc})"
        html = resp.text
        m = re.search(r'<meta\s+name="description"\s+content="([^"]+)"', html)
        if m:
            return f"(public overview of {url})\n\n{m.group(1)}"
        return f"(public overview of {url} — content not extractable; paste manually into PROBLEM_STATEMENT.md)"

    # --- data ---------------------------------------------------------------

    def download(self, slug: str, dest: Path, force: bool = False) -> Path:
        dest.mkdir(parents=True, exist_ok=True)
        args = ["competitions", "download", slug, "--path", str(dest), "--quiet"]
        if force:
            args.append("--force")
        self._run(args, timeout=3600)
        self._extract_zips(dest)
        return dest

    @staticmethod
    def _extract_zips(dest: Path) -> list[Path]:
        extracted: list[Path] = []
        for zpath in sorted(dest.glob("*.zip")):
            marker = dest / f"{zpath.stem}.extracted"
            if marker.exists():
                continue
            try:
                with zipfile.ZipFile(zpath) as zf:
                    zf.extractall(dest)
                marker.touch()
                extracted.append(zpath)
            except zipfile.BadZipFile:
                continue
        return extracted

    def submit(self, slug: str, file: Path, message: str = "") -> str:
        out = self._run(
            ["competitions", "submit", slug, "--file", str(file), "--message", message or "engine"],
            timeout=600,
        )
        return out.strip()

    def submissions(self, slug: str) -> list[dict[str, Any]]:
        data = self._run_json(["competitions", "submissions", slug]) or []
        return data if isinstance(data, list) else []

    def best_public_score(self, slug: str) -> float | None:
        """Best finished public score from our submission history."""
        best: float | None = None
        for sub in self.submissions(slug):
            raw = sub.get("publicScore") or sub.get("public_score")
            status = str(sub.get("status", "")).lower()
            if raw in (None, "") or "pending" in status or "error" in status:
                continue
            try:
                value = float(raw)
            except ValueError:
                continue
            if best is None or value > best:
                best = value
        return best

    def leaderboard(self, slug: str, top: int = 50) -> list[dict[str, Any]]:
        data = self._run_json(["competitions", "leaderboard", slug, "--page-size", str(top)]) or []
        return data if isinstance(data, list) else []

    def leaderboard_percentile(self, slug: str, score: float, higher_is_better: bool = True) -> dict[str, Any]:
        """Where would `score` sit on the full public leaderboard?"""
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            self._run(["competitions", "leaderboard", slug, "--download", "--path", tmp, "--quiet"],
                      timeout=600)
            values: list[float] = []
            for csv_path in Path(tmp).glob("*.csv"):
                with csv_path.open(newline="", encoding="utf-8") as fh:
                    for row in csv.DictReader(fh):
                        for key in ("PublicScore", "publicScore", "Score", "score"):
                            if key in row and row[key]:
                                try:
                                    values.append(float(row[key]))
                                except ValueError:
                                    pass
                                break
        if not values:
            return {"available": False}
        beaten = (sum(1 for v in values if v < score) if higher_is_better
                  else sum(1 for v in values if v > score))
        return {
            "available": True,
            "entries": len(values),
            "percentile": round(100.0 * beaten / len(values), 2),
            "top_score": max(values) if higher_is_better else min(values),
            "median_score": sorted(values)[len(values) // 2],
        }


def _extract_text(data: Any) -> str:
    """Recursively pull human-readable content out of unknown JSON shapes."""
    chunks: list[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, str):
            if len(node.strip()) > 40:  # page content, not a label
                chunks.append(node.strip())
        elif isinstance(node, dict):
            for key in ("content", "body", "text", "markdown", "value"):
                if key in node:
                    walk(node[key])
            for key, value in node.items():
                if key not in ("content", "body", "text", "markdown", "value"):
                    walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(data)
    # De-duplicate while preserving order.
    seen: set[str] = set()
    out = []
    for chunk in chunks:
        if chunk not in seen:
            seen.add(chunk)
            out.append(chunk)
    return "\n\n".join(out)


def csv_output_to_rows(text: str) -> list[dict[str, str]]:
    """Parse `--csv` CLI table output (used as a fallback when json fails)."""
    return list(csv.DictReader(io.StringIO(text)))
