"""Prompt construction for the coder agent (OpenCode).

Two message types:

* **coder task** — "write/repair the notebook for this competition, under the
  rulebook, until the score gate is met."
* **ask** — "answer this question about the competition sources", which is how
  the engine holds a conversation with the coder about the problem statement,
  the datasets and the leaderboard.

The scout brief (problem statement + dataset profile) is attached as a file, so
the message itself stays short enough for a Windows command line.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import rules
from .settings import Settings


def coder_system_prompt() -> str:
    return (
        "You are the coding agent of the Kaggle engine. You write competition "
        "notebooks that are correct, leak-free and reproducible, and you report "
        "honestly: no measured number is ever invented.\n\n"
        f"Rulebook v{rules.RULEBOOK_VERSION} (binding, in priority order):\n"
        f"{rules.as_digest()}\n\n"
        "Working style: read the attached brief first; inspect the actual CSVs in "
        "../datasets/ before assuming a schema; prefer a working baseline over a "
        "clever one; every claim in your final message must be traceable to a file "
        "you wrote. If something blocks you (missing data, unclear metric), say so "
        "explicitly in your final message instead of guessing."
    )


def _brief_block(brief: dict[str, Any] | None, brief_path: Path | None) -> str:
    if brief is None:
        return "Brief: not available — read PROBLEM_STATEMENT.md and ../datasets/ directly."
    files = brief.get("files") or []
    file_names = ", ".join(
        (item.get("name") or item.get("ref") or "?") for item in files[:12]
    ) or "unknown"
    prof = brief.get("profiles") or []
    shapes = "; ".join(
        f"{p.get('file')} {p.get('rows')}x{p.get('cols')}" for p in prof if "error" not in p
    ) or "none profiled"
    return (
        f"Competition: {brief.get('title') or brief.get('slug')} ({brief.get('slug')})\n"
        f"URL: {brief.get('url')}\n"
        f"Metric: {brief.get('metric')} (higher_is_better={brief.get('higher_is_better')})\n"
        f"Target column: {brief.get('target')}\n"
        f"Score gate: {brief.get('target_score')}\n"
        f"Files: {file_names}\n"
        f"Datasets on disk: {shapes}\n"
        f"Brief file to read: {brief_path}\n"
        f"Problem statement file: PROBLEM_STATEMENT.md"
    )


def coder_task_prompt(
    slug: str,
    brief: dict[str, Any] | None,
    attempt: int,
    feedback: str | None = None,
    brief_path: Path | None = None,
    settings: Settings | None = None,
) -> str:
    settings = settings or __import__("engine.settings", fromlist=["load"]).load()
    notebook = f"competition/{slug}/code/{slug}.pynb"
    parts = [
        f"# Task — write the Kaggle solution notebook for `{slug}` (attempt {attempt}/{settings.max_attempts})",
        "",
        "## Attached context",
        "",
        _brief_block(brief, brief_path),
        "",
        "## Deliverables (rule R1/R13)",
        "",
        f"1. `{notebook}` — the single source artifact. Extend the existing baseline "
        "in place; keep it runnable top-to-bottom with the `python3` kernel.",
        f"2. `competition/{slug}/readme.md` — keep sections 2–5 accurate per rule R11 "
        "(algorithm walkthrough, score table, rejected ideas, next steps).",
        "",
        "## Contract the notebook must honour",
        "",
        "* Reads only from `../datasets/`; writes only into `../train/`.",
        "* Writes `../train/metrics.json` with: metric, task, cv_mean, cv_std, cv_folds, "
        "oof_score, n_splits, n_train, n_test, seed, models (list), runtime_sec, "
        "target_score, higher_is_better.",
        "* Writes `../train/submission.csv` matching `sample_submission.csv` when a test "
        "set exists.",
        "* Leaves `../train/oof_<model>.csv` and `../train/importance_<model>.csv`.",
        "* No credentials, no uploads, no network beyond Kaggle data already on disk.",
        "* Deterministic: one SEED constant seeds every library (R3).",
        "",
        "## How to spend this attempt",
        "",
        f"* Attempt 1: make the leak-free baseline real and measured (R7 steps 1–3).",
        f"* Later attempts: climb the ladder — model zoo (LightGBM/XGBoost/CatBoost), "
        "OOF-fitted ensemble, fold-safe target encoding, pseudo-labelling, bounded search.",
        "* Prefer more evidence over more models: if the CV-vs-gate gap is unexplained, "
        "fix the measurement before adding capacity (R5).",
    ]
    if feedback:
        parts += [
            "",
            "## Feedback from the previous attempt (act on this)",
            "",
            feedback.strip(),
        ]
    parts += [
        "",
        "## Final message format",
        "",
        "End your turn with a short report in markdown: what you changed, the measured "
        "OOF score if you have one (from `../train/metrics.json`), what you tried and "
        "rejected, what you need next, and any question about the competition sources. "
        "The engine stores this message as the communication record for the attempt.",
    ]
    return "\n".join(parts)


def ask_prompt(slug: str, question: str, brief: dict[str, Any] | None,
               brief_path: Path | None = None) -> str:
    return "\n".join([
        f"# Question about the competition sources — `{slug}`",
        "",
        _brief_block(brief, brief_path),
        "",
        "## Question",
        "",
        question.strip(),
        "",
        "## How to answer",
        "",
        "Ground the answer in the files on disk: read `PROBLEM_STATEMENT.md`, the CSVs "
        "in `../datasets/`, and `../train/metrics.json` if it exists. Quote concrete "
        "numbers and column names. If the sources do not contain the answer, say so and "
        "state exactly which Kaggle page or file would (rule R4: never invent facts).",
    ])


def load_brief(slug: str, settings: Settings | None = None) -> dict[str, Any] | None:
    settings = settings or __import__("engine.settings", fromlist=["load"]).load()
    path = settings.train_dir(slug) / "brief.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        return None
