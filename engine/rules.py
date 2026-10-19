"""The rulebook every engine run obeys (rules R1–R13).

The rules are versioned. Each run records the rules version, so a score can
always be traced back to the contract it was produced under. The full text is
injected into every coder prompt — see :mod:`engine.prompts`.
"""

from __future__ import annotations

RULEBOOK_VERSION = "1.0.0"

# (id, title, text)
RULES: list[tuple[str, str, str]] = [
    (
        "R1",
        "Folder contract",
        "Every deliverable lives under competition/<slug>/: code/<slug>.pynb is the ONLY "
        "source artifact; datasets/ is read-only Kaggle data; train/ holds all run outputs; "
        "readme.md is the write-up. Never write outside the competition folder, never touch "
        ".engine/, frontend/data belongs to the report step only, and the legacy NTG/ folder "
        "does not exist (rule R10).",
    ),
    (
        "R2",
        "One notebook, top to bottom",
        "code/<slug>.pynb must run cleanly top-to-bottom on a fresh machine after "
        "`pip install -r requirements.txt`, kernel 'python3'. No manual steps, no hidden "
        "state between runs, no network access except reading ../datasets/, no uploads.",
    ),
    (
        "R3",
        "Determinism",
        "One SEED constant at the top seeds python, numpy, sklearn, lightgbm, xgboost and "
        "catboost. The same commit and seed must reproduce the same CV score.",
    ),
    (
        "R4",
        "Honest measurement",
        "Only report scores that were actually measured. The CV score comes from out-of-fold "
        "predictions, never from training-set predictions. Every run writes train/metrics.json "
        "(metric, task, cv_mean, cv_std, cv_folds, n_train, n_test, seed, n_splits, models, "
        "runtime_sec). A number that is not in an artifact is not a result.",
    ),
    (
        "R5",
        "Score matching gate",
        "A competition counts as solved only when the OOF score meets the target score "
        "(default: user-set or leaderboard-derived; recorded per competition in the engine "
        "store). Always record the CV-vs-leaderboard gap; if the gap is large (> 2x the CV "
        "std), diagnose the split (duplicates, group leakage, distribution shift) BEFORE "
        "adding more models.",
    ),
    (
        "R6",
        "Leakage discipline",
        "No target-dependent transform may run before the split. Target/category encodings "
        "must be fold-safe (computed excluding the row's own fold). Assert every training row "
        "received exactly one OOF prediction. Use group-aware or time-aware folds when ids or "
        "timestamps make random folds leak.",
    ),
    (
        "R7",
        "Optimization ladder",
        "Improve in this order and stop when the gate is met: (1) clean leak-free baseline, "
        "(2) sanity-check folds and metric implementation, (3) domain feature engineering from "
        "the problem statement, (4) model zoo — LightGBM, XGBoost, CatBoost, (5) OOF-fitted "
        "ensemble (rank-mean for rank-based metrics, hill-climb weights otherwise), (6) "
        "fold-safe target encodings, (7) pseudo-labelling / self-training, (8) bounded "
        "hyperparameter search with a fixed seed budget. Never jump to (8) before (1)–(4).",
    ),
    (
        "R8",
        "Resource budget",
        "CPU only by default. One notebook execution must finish within ENGINE_NOTEBOOK_TIMEOUT "
        "(default 1h). Subsample while iterating, use the full dataset on the final attempt. "
        "A cycle makes at most ENGINE_MAX_ATTEMPTS coder attempts.",
    ),
    (
        "R9",
        "Submission policy",
        "Notebooks never upload anything. Submissions go through the engine, only when "
        "ENGINE_SUBMIT_ENABLED=1, respecting daily submission limits, and every submission is "
        "logged in the engine store.",
    ),
    (
        "R10",
        "Legacy folder",
        "The NTG/ folder is a historical trial-and-error workspace. Never read from it, never "
        "write to it, never reference its contents in prompts, code or reports.",
    ),
    (
        "R11",
        "README write-up",
        "competition/<slug>/readme.md must contain: (a) problem summary and metric and why it "
        "matters, (b) algorithm walkthrough — features, folds, models, ensemble, (c) the score "
        "table copied from train/metrics.json — OOF mean/std/folds, leaderboard, target, gap, "
        "(d) what was tried and rejected with numbers, (e) ranked next steps. Never paste a "
        "score that is not in an artifact.",
    ),
    (
        "R12",
        "Security",
        "Never hard-code, print or commit credentials. Kaggle access comes from env vars or "
        "~/.kaggle/kaggle.json only. No secrets in notebooks, READMEs, logs or synced data. "
        "Datasets/ and train/ artifacts never enter git (.gitignore enforces it).",
    ),
    (
        "R13",
        "Reproducible artifacts",
        "Every executed attempt leaves behind: train/metrics.json, train/submission.csv (when "
        "produced), train/oof_<model>.csv, train/importance_<model>.csv, the executed notebook "
        "copy, and the attempt log — so any number in the README can be traced to its run.",
    ),
]


def as_markdown() -> str:
    lines = [f"# Engine rulebook v{RULEBOOK_VERSION}", ""]
    for rid, title, text in RULES:
        lines.append(f"## {rid} — {title}")
        lines.append("")
        lines.append(text)
        lines.append("")
    return "\n".join(lines)


def as_digest() -> str:
    """Compact one-line-per-rule form for prompt injection."""
    return "\n".join(f"{rid} [{title}]: {text}" for rid, title, text in RULES)


def by_id(rule_id: str) -> tuple[str, str, str] | None:
    for rule in RULES:
        if rule[0] == rule_id:
            return rule
    return None
