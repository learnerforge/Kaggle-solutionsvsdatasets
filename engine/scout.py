"""Scout — the agent that stays alive to the competition.

It gathers what the coder needs *before* any code exists:

* problem statement, evaluation page and rules text from Kaggle,
* the competition file list,
* the datasets themselves (Kaggle CLI, into ``competition/<slug>/datasets/``),
* a schema/missingness/target profile of every CSV,
* a detected target column and metric direction.

Output: ``PROBLEM_STATEMENT.md``, ``BRIEF.md`` and ``train/brief.json`` inside
the competition folder. Everything degrades gracefully: no credentials or no
network means the brief still contains whatever is on disk, plus a warning.
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from . import profile, store
from .kaggle_client import KaggleCLIError, KaggleClient
from .settings import Settings, load

# Metric names as they appear in Kaggle evaluation pages, most specific first.
_METRIC_PATTERNS: list[tuple[str, str]] = [
    ("roc auc", "roc_auc"),
    ("area under the roc", "roc_auc"),
    ("log loss", "log_loss"),
    ("logloss", "log_loss"),
    ("balanced accuracy", "balanced_accuracy"),
    ("root mean squared error", "rmse"),
    ("rmse", "rmse"),
    ("mean squared error", "mse"),
    ("mean absolute error", "mae"),
    ("mae", "mae"),
    ("quadratic weighted kappa", "quadratic_weighted_kappa"),
    ("f1", "f1"),
    ("accuracy", "accuracy"),
]

_LOWER_IS_BETTER = {"rmse", "mse", "mae", "log_loss", "rmsle"}


@dataclass
class Brief:
    slug: str
    title: str | None
    url: str
    metric: str | None
    higher_is_better: bool
    target: str | None
    target_score: float | None
    problem_statement: str
    files: list[dict[str, Any]] = field(default_factory=list)
    profiles: list[dict[str, Any]] = field(default_factory=list)
    parity: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    gathered_at: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def detect_metric(text: str) -> str | None:
    low = text.lower()
    for needle, metric in _METRIC_PATTERNS:
        if needle in low:
            return metric
    return None


def _detect_target_from_files(datasets_dir: Path, declared: str | None) -> str | None:
    train_path = next(iter(sorted(datasets_dir.glob("train*.csv"))), None)
    if train_path is None:
        return declared
    try:
        train_cols = pd.read_csv(train_path, nrows=5).columns.tolist()
    except Exception:  # noqa: BLE001
        return declared
    sub_path = next(iter(sorted(datasets_dir.glob("sample_submission*.csv"))), None)
    sub_cols = None
    if sub_path is not None:
        try:
            sub_cols = pd.read_csv(sub_path, nrows=5).columns.tolist()
        except Exception:  # noqa: BLE001
            sub_cols = None
    return profile.detect_target(train_cols, sub_cols, declared)


def _read_problem_statement(competition_dir: Path) -> str:
    path = competition_dir / "PROBLEM_STATEMENT.md"
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def scout(
    slug: str,
    *,
    download: bool = True,
    refresh: bool = False,
    wait_join: int = 0,
    title: str | None = None,
    target: str | None = None,
    metric: str | None = None,
    target_score: float | None = None,
    settings: Settings | None = None,
) -> Brief:
    settings = settings or load()
    comp_dir = settings.competition_dir(slug)
    datasets_dir = settings.datasets_dir(slug)
    train_dir = settings.train_dir(slug)
    for directory in (comp_dir / "code", datasets_dir, train_dir):
        directory.mkdir(parents=True, exist_ok=True)
        if directory.name in {"datasets", "train"}:
            (directory / ".gitkeep").touch(exist_ok=True)

    registered = store.get_competition(slug, settings) or {}
    title = title or registered.get("title")
    target = target or registered.get("target")
    if not target:
        # The store has no target column; the last brief is the memory for it.
        # Without this a plain `engine scout` (no --target) would overwrite a
        # known target with null and the coder prompt would lose it.
        try:
            previous = json.loads((train_dir / "brief.json").read_text(encoding="utf-8"))
            target = previous.get("target") or None
        except (OSError, ValueError, TypeError):
            pass
    metric = metric or registered.get("metric")
    target_score = (target_score if target_score is not None
                    else registered.get("target_score", settings.default_target_score))

    warnings: list[str] = []
    files: list[dict[str, Any]] = []

    statement_path = comp_dir / "PROBLEM_STATEMENT.md"
    statement = _read_problem_statement(comp_dir)
    if refresh or not statement:
        try:
            client = KaggleClient(settings)
            files = client.files(slug)
            fetched = client.problem_statement(slug)
            if fetched.strip():
                statement = fetched
                statement_path.write_text(
                    f"# Problem statement — {title or slug}\n\n"
                    f"> Fetched from Kaggle on {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC}.\n"
                    f"> Kaggle: https://www.kaggle.com/competitions/{slug}\n\n{statement}\n",
                    encoding="utf-8",
                )
            else:
                warnings.append("Kaggle returned an empty problem statement; add it to PROBLEM_STATEMENT.md manually.")
        except KaggleCLIError as exc:
            warnings.append(f"Kaggle metadata unavailable: {exc}")
            statement = statement or f"(problem statement not fetched — {exc})"
    else:
        try:
            files = KaggleClient(settings).files(slug)
        except KaggleCLIError as exc:
            warnings.append(f"Kaggle file list unavailable: {exc}")

    # --- datasets ---------------------------------------------------------
    if download:
        has_data = any(datasets_dir.glob("*.csv")) or any(datasets_dir.glob("*.parquet"))
        if not has_data:
            def _on_wait(attempt: int, remaining: int) -> None:
                print(f"[scout] rules not accepted yet — waiting for the join "
                      f"({remaining}s left, attempt {attempt}); accept them at "
                      f"https://www.kaggle.com/competitions/{slug}",
                      file=sys.stderr, flush=True)

            try:
                KaggleClient(settings).download(slug, datasets_dir,
                                                wait=wait_join, on_wait=_on_wait)
            except KaggleCLIError as exc:
                warnings.append(f"Dataset download failed: {exc}")

    # --- profile ----------------------------------------------------------
    target = _detect_target_from_files(datasets_dir, target)
    profiles = profile.profile_datasets_dir(datasets_dir, target=target)

    train_path = next(iter(sorted(datasets_dir.glob("train*.csv"))), None)
    test_path = next(iter(sorted(datasets_dir.glob("test*.csv"))), None)
    parity: dict[str, Any] = {}
    if train_path and test_path:
        try:
            train_df = pd.read_csv(train_path, nrows=200_000)
            test_df = pd.read_csv(test_path, nrows=200_000)
            parity = profile.compare_train_test(train_df, test_df, target=target)
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"train/test comparison failed: {exc}")

    detected_metric = detect_metric(statement) if statement else None
    if detected_metric:
        metric = detected_metric
    metric = metric or registered.get("metric")
    higher_is_better = (metric not in _LOWER_IS_BETTER) if metric else True

    brief = Brief(
        slug=slug,
        title=title,
        url=f"https://www.kaggle.com/competitions/{slug}",
        metric=metric,
        higher_is_better=higher_is_better,
        target=target,
        target_score=target_score,
        problem_statement=statement,
        files=files,
        profiles=profiles,
        parity=parity,
        warnings=warnings,
        gathered_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )

    store.register_competition(
        slug, title=title, metric=metric, higher_is_better=higher_is_better,
        target_score=target_score, settings=settings,
    )

    train_dir.mkdir(parents=True, exist_ok=True)
    (train_dir / "brief.json").write_text(json.dumps(brief.as_dict(), indent=2), encoding="utf-8")
    (comp_dir / "BRIEF.md").write_text(render_brief(brief), encoding="utf-8")
    return brief


def render_brief(brief: Brief) -> str:
    """Markdown brief — also attached to the opencode message."""
    lines: list[str] = [
        f"# Competition brief — {brief.title or brief.slug}",
        "",
        f"* Kaggle: <{brief.url}>",
        f"* Slug: `{brief.slug}`",
        f"* Detected metric: `{brief.metric or 'unknown'}` "
        f"({'higher' if brief.higher_is_better else 'lower'} is better)",
        f"* Target column: `{brief.target or 'unknown'}`",
        f"* Score gate: `{brief.target_score if brief.target_score is not None else 'not set'}`",
        f"* Gathered: {brief.gathered_at}",
        "",
        "## Files",
        "",
    ]
    if brief.files:
        lines += ["| file | size (bytes) |", "| --- | --- |"]
        for item in brief.files[:60]:
            name = item.get("name") or item.get("ref") or "?"
            size = item.get("totalBytes") or item.get("total_bytes") or item.get("size") or "?"
            lines.append(f"| `{name}` | {size} |")
    else:
        lines.append("_No file list available (offline or not authenticated)._")

    lines += ["", "## Dataset profile", "", profile.render_markdown(brief.profiles) or "_No CSVs found._"]

    if brief.parity:
        lines += [
            "",
            "## Train/test parity",
            "",
            f"* shared columns: {brief.parity.get('shared_cols')}",
            f"* only in train: {brief.parity.get('only_train') or 'none'}",
            f"* only in test: {brief.parity.get('only_test') or 'none'}",
            f"* id overlap: {brief.parity.get('id_column_overlap')}",
            f"* numeric drift (|mean shift| / std > 0.5): {brief.parity.get('numeric_drift') or 'none'}",
        ]

    if brief.warnings:
        lines += ["", "## Warnings", ""] + [f"* {w}" for w in brief.warnings]

    lines += [
        "",
        "## Problem statement",
        "",
        brief.problem_statement.strip() or "_not available — paste it into PROBLEM_STATEMENT.md_",
        "",
    ]
    return "\n".join(lines)


def pick_daily(settings: Settings | None = None) -> str | None:
    """Choose the next problem statement for a daily cycle.

    Priority: (1) a competition already on disk that is not solved,
    (2) an unfinished competition in the store, (3) a fresh Kaggle competition
    (recent playground series), skipping anything already attempted.
    """
    settings = settings or load()
    known = {c["slug"]: c for c in store.list_competitions(settings)}

    on_disk = sorted(p.name for p in settings.competitions_root.iterdir()
                     if p.is_dir()) if settings.competitions_root.is_dir() else []
    for slug in on_disk:
        if known.get(slug, {}).get("status") != "solved":
            return slug

    for slug, comp in known.items():
        if comp.get("status") != "solved":
            return slug

    try:
        client = KaggleClient(settings)
        for candidate in client.list_competitions(search="playground", category="playground", page_size=20):
            slug = candidate.get("slug", "")
            if slug and slug not in known:
                return slug
    except KaggleCLIError:
        return None
    return None
