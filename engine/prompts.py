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


# --------------------------------------------------------------------------- #
# metric playbooks — concrete algorithm ladders per scoring metric
# --------------------------------------------------------------------------- #

_METRIC_PLAYBOOKS: list[tuple[tuple[str, ...], str]] = [
    (("rmse", "mse", "mae", "rmsle"),
     "* Baseline first: median/most-frequent prediction, then regularised linear "
     "model (Ridge/ElasticNet) on one-hot or ordinal encoding — that number is "
     "your honesty anchor (R7).\n"
     "* Skewed target (check `profiles` in the brief): model `log1p(y)` and "
     "expm1 back — for RMSE-on-price-style targets this alone often beats a "
     "model upgrade. Report the metric on the original scale (R5).\n"
     "* Gradient boosting ladder: LightGBM -> XGBoost -> CatBoost (CatBoost for "
     "high-cardinality categoricals without manual encoding). Keep folds, SEED "
     "and features identical across the zoo so the comparison is fair.\n"
     "* Blend only with OOF evidence: fit each member on the same K folds, "
     "average predictions by a weight chosen on OOF (start 50/50 or 60/40), "
     "and keep the blend's OOF score — never a test-set-tuned weight.\n"
     "* Watch the CV-vs-gate gap before adding capacity: duplicated rows, a "
     "leaky column, or a fold mismatch (R6) distorts RMSE more than any model choice."),
    (("f1",),
     "* Text or binary-classification F1: start with TF-IDF (word 1-2 grams + "
     "char 3-5 grams) -> LogisticRegression / LinearSVC. This baseline is "
     "strong and trains in seconds; measure it before any neural model.\n"
     "* F1 depends on the decision threshold, not just the model: choose the "
     "threshold that maximises F1 **on OOF predictions only** (grid ~0.20-0.80 "
     "in 0.01 steps), then freeze it for the test set. Never tune on test.\n"
     "* Stratified folds (R6) so every fold carries both classes; verify each "
     "fold's positive rate in the brief's target profile.\n"
     "* Model ladder after the linear baseline: fine-tuned compact transformer "
     "(if GPU/time allows) or stacked TF-IDF + LightGBM on the same OOF; any "
     "ensemble must be decided on OOF F1, not test predictions.\n"
     "* Output must match `sample_submission.csv` exactly: same row order, "
     "same `id` values, integer 0/1 predictions."),
    (("roc_auc", "auc"),
     "* ROC AUC only needs correct ordering, not calibrated probabilities and "
     "not any threshold: never round or threshold the predictions before scoring.\n"
     "* Baseline: LightGBM/XGBoost with conservative defaults; then feature "
     "work (target encoding fold-safe, interaction features) usually beats "
     "hyperparameter sweeps at this metric.\n"
     "* Aggregated/mean-shifted features and time-safe joins matter: check the "
     "brief's numeric drift and only-train/only-test columns before adding them.\n"
     "* Ensemble: rank-average or mean-blend member models on OOF AUC; report "
     "the blended OOF, not the best single test submission."),
    (("log_loss",),
     "* Log loss rewards well-calibrated probabilities: prefer models with "
     "native probability output; if blending, average **probabilities** (not "
     "labels) and verify calibration on OOF.\n"
     "* Guard against confident errors: clip predicted probabilities to "
     "[1e-5, 1-1e-5] and confirm class order matches the sample submission.\n"
     "* Use stratified folds; a fold missing a class explodes the loss (R6)."),
    (("accuracy", "balanced_accuracy"),
     "* Stratified folds and a per-fold metric print are mandatory — with "
     "imbalanced classes accuracy hides failure (check the target profile).\n"
     "* Choose the decision threshold on OOF (maximise the metric or move it "
     "toward balanced accuracy), freeze it, then apply to test.\n"
     "* Ladder: regularised linear baseline -> LightGBM/XGBoost -> OOF blend."),
    (("quadratic_weighted_kappa",),
     "* QWK needs integer-ish predictions: model as regression (or ordinal) and "
     "round/clamp to the allowed label range before computing the metric.\n"
     "* The known QWK trick: start from your model's OOF predictions and search "
     "an order-preserving mapping (thresholds) that maximises QWK **on OOF**, "
     "then apply the frozen mapping to test.\n"
     "* Keep folds identical across variants — QWK is sensitive to fold "
     "composition with few distinct labels."),
]

_GENERIC_PLAYBOOK = (
    "* Establish a measured, leak-free baseline on fixed folds first (R7 steps 1-3); "
    "an unmeasured model is not a result (R4).\n"
    "* Then climb the ladder: regularised linear model -> LightGBM/XGBoost/CatBoost -> "
    "OOF-fitted blend, changing one variable per attempt so every score delta is attributable.\n"
    "* All tuning decisions are made on OOF predictions only; test predictions are "
    "produced once, by the frozen pipeline (R6)."
)


def metric_playbook(metric: str | None) -> str:
    """Concrete algorithm ladder for the competition's metric (prompt depth)."""
    low = (metric or "").lower().strip()
    for family, text in _METRIC_PLAYBOOKS:
        if low in family:
            return text
    return _GENERIC_PLAYBOOK


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
    notebook = f"competition/{slug}/code/{slug}.ipynb"
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
        "* Saves the trained model to `../train/model.joblib` (fitted estimators, "
        "re-loadable without retraining — every notebook ships a model, rule R13).",
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
    metric = (brief or {}).get("metric")
    parts += [
        "",
        f"## Algorithm playbook — metric `{metric or 'unknown'}`",
        "",
        metric_playbook(metric),
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
