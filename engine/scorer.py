"""Score matching — the gate that decides whether a competition is solved.

Rule R5: a competition counts as solved only when the measured out-of-fold
score meets the target. Rule R7: when it is not met, feedback to the coder
follows the optimization ladder instead of "try harder".

The scorer never produces a score itself; it reads ``train/metrics.json`` (the
only source of truth, rule R4) and optionally the leaderboard.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path

from . import store
from .kaggle_client import KaggleCLIError, KaggleClient
from .settings import Settings, load

LOWER_IS_BETTER = {"rmse", "mse", "mae", "logloss", "log_loss", "neg_log_loss", "rmsle", "error"}


@dataclass
class ScoreReport:
    slug: str
    metric: str | None = None
    task: str | None = None
    cv_mean: float | None = None
    cv_std: float | None = None
    cv_folds: list[float] = field(default_factory=list)
    oof_score: float | None = None
    lb_score: float | None = None
    target_score: float | None = None
    higher_is_better: bool = True
    reached: bool | None = None
    gap: float | None = None          # normalised: positive means LB better than OOF
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return asdict(self)

    def summary(self) -> str:
        if self.cv_mean is None:
            return f"{self.slug}: no measured score yet"
        direction = ">=" if self.higher_is_better else "<="
        gate = ("gate not set" if self.target_score is None
                else f"gate {direction} {self.target_score}: "
                     f"{'REACHED' if self.reached else 'NOT reached'}")
        lb = "" if self.lb_score is None else f", LB {self.lb_score:.5f}"
        return (f"{self.slug}: OOF {self.metric} {self.cv_mean:.5f} "
                f"+/- {self.cv_std if self.cv_std is None else format(self.cv_std, '.5f')}"
                f"{lb} ({gate})")


def direction_for(metric: str | None, default: bool = True) -> bool:
    if not metric:
        return default
    return metric.lower() not in LOWER_IS_BETTER


def load_metrics(slug: str, settings: Settings | None = None) -> dict | None:
    settings = settings or load()
    import json

    path = settings.train_dir(slug) / "metrics.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


def evaluate(slug: str, *, target_score: float | None = None, fetch_lb: bool = False,
             settings: Settings | None = None) -> ScoreReport:
    settings = settings or load()
    registered = store.get_competition(slug, settings) or {}
    metrics = load_metrics(slug, settings)
    report = ScoreReport(slug=slug)

    target = target_score
    if target is None and metrics is not None:
        target = metrics.get("target_score")
    if target is None:
        target = registered.get("target_score", settings.default_target_score)

    if metrics is None:
        report.metric = registered.get("metric")
        report.higher_is_better = bool(registered.get("higher_is_better", True))
        report.target_score = target
        report.notes.append("train/metrics.json missing — nothing measured yet (rule R4)")
        return report

    report.metric = metrics.get("metric") or registered.get("metric")
    report.task = metrics.get("task")
    report.cv_mean = _as_float(metrics.get("cv_mean"))
    report.cv_std = _as_float(metrics.get("cv_std"))
    report.cv_folds = [v for v in (metrics.get("cv_folds") or []) if isinstance(v, (int, float))]
    oof = _as_float(metrics.get("oof_score"))
    report.oof_score = oof if oof is not None else report.cv_mean
    report.higher_is_better = bool(metrics.get("higher_is_better",
                                               direction_for(report.metric)))
    report.target_score = target

    if report.cv_std is not None and report.cv_std > 0.01:
        report.notes.append(
            f"fold std {report.cv_std:.5f} is high — the CV estimate is noisy; "
            "more folds or repeated CV would price the uncertainty properly"
        )
    if report.cv_folds:
        worst = min(report.cv_folds) if report.higher_is_better else max(report.cv_folds)
        report.notes.append(f"worst fold: {worst:.5f} (that is what a bad leaderboard day looks like)")

    if fetch_lb:
        try:
            report.lb_score = KaggleClient(settings).best_public_score(slug)
        except KaggleCLIError as exc:
            report.notes.append(f"leaderboard unavailable: {exc}")
    if report.lb_score is not None and report.cv_mean is not None:
        signed = report.lb_score - report.cv_mean
        report.gap = round(signed if report.higher_is_better else -signed, 6)
        if report.gap < -0.002 and report.cv_std is not None and abs(report.gap) > 2 * report.cv_std:
            report.notes.append(
                "OOF is materially better than the public LB — suspect split mismatch "
                "(duplicates, group leakage, distribution shift). Diagnose before adding models (R5)"
            )

    if report.target_score is not None and report.cv_mean is not None:
        report.reached = (report.cv_mean >= report.target_score if report.higher_is_better
                          else report.cv_mean <= report.target_score)
    return report


def build_feedback(
    report: ScoreReport,
    checks: dict | None = None,
    execution_error: str | None = None,
    *,
    settings: Settings | None = None,
) -> str:
    """Feedback for the next coder attempt — always ordered by R7."""
    settings = settings or load()
    lines: list[str] = []

    if checks and checks.get("failed"):
        lines.append("### Structural failures (fix these first — they outrank score)")
        for check in checks["checks"]:
            if check["status"] == "fail":
                lines.append(f"* **{check['rule']} {check['title']}** — {check['detail']}")
        lines.append("")

    if execution_error:
        lines.append("### The notebook did not finish executing")
        lines.append("```")
        lines.append(execution_error.strip()[-2500:])
        lines.append("```")
        lines.append("Repair the failing cell, then re-run from the top. Do not work around it by "
                     "deleting cells — the artifacts in `../train/` are still required (R13).")
        lines.append("")

    if report.cv_mean is None:
        lines.append("### No measured score")
        lines.append("`../train/metrics.json` was not produced, so nothing can be compared to the "
                     "gate. Get a complete, honest baseline run first (R4), even if the score is low.")
        return "\n".join(lines)

    if report.reached:
        lines.append("### Gate reached")
        lines.append(f"{report.metric} OOF {report.cv_mean:.5f} meets the target "
                     f"{report.target_score}. Freeze this configuration, keep the artifacts, and only "
                     "change things that are measured to help (R4). Document the final choice in readme.md (R11).")
        return "\n".join(lines)

    metrics = load_metrics(report.slug, settings) or {}
    models = metrics.get("models") or []
    notes = report.notes or []

    lines.append("### Gate not reached — climb the R7 ladder")
    lines.append(f"Measured OOF {report.metric}: `{report.cv_mean:.5f}` "
                 f"(std {report.cv_std if report.cv_std is None else round(report.cv_std, 5)}), "
                 f"target `{report.target_score}`. Gap: "
                 f"{abs(report.target_score - report.cv_mean):.5f}.")
    lines.append("")

    suggestions: list[str] = []
    if report.cv_std is not None and report.cv_std > 0.01:
        suggestions.append("CV is noisy (step 2): more folds or repeated CV before any modelling change.")
    if len(models) < 3:
        suggestions.append(f"Model zoo incomplete (step 4): currently {models or ['none']}. Add "
                           "LightGBM + XGBoost + CatBoost, each with its own metrics entry.")
    if "ensemble" not in metrics:
        suggestions.append("No ensemble recorded (step 5): blend OOF predictions — rank-mean for "
                           "rank metrics, hill-climb weights fitted on OOF only.")
    if not metrics.get("target_encoding"):
        suggestions.append("Consider fold-safe target/category encoding for high-cardinality columns "
                           "(step 6) — computed excluding each row's own fold.")
    if not metrics.get("pseudo_labelling"):
        suggestions.append("Consider pseudo-labelling confident test rows (step 7), validated on OOF.")
    suggestions.append("Only now, with steps 1–4 clean and measured, spend a bounded seed budget on "
                       "hyperparameters (step 8) — and record the search space in metrics.json.")

    lines += [f"* {s}" for s in suggestions]
    if notes:
        lines += ["", "### Diagnostics"] + [f"* {n}" for n in notes]
    return "\n".join(lines)


def maybe_submit(slug: str, *, message: str = "", settings: Settings | None = None) -> dict:
    """R9: submissions only when ENGINE_SUBMIT_ENABLED=1, always logged."""
    settings = settings or load()
    submission = settings.train_dir(slug) / "submission.csv"
    if not settings.submit_enabled:
        return {"submitted": False, "reason": "ENGINE_SUBMIT_ENABLED is not set (rule R9)"}
    if not submission.is_file():
        return {"submitted": False, "reason": f"no submission file at {submission}"}
    try:
        client = KaggleClient(settings)
        output = client.submit(slug, submission, message=message or "engine cycle")
        score = client.best_public_score(slug)
        store.log_submission(slug, message, score, settings)
        return {"submitted": True, "output": output.strip()[-1500:], "best_public_score": score}
    except KaggleCLIError as exc:
        return {"submitted": False, "reason": str(exc)}


def _as_float(value: object) -> float | None:
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def metrics_path(slug: str, settings: Settings | None = None) -> Path:
    settings = settings or load()
    return settings.train_dir(slug) / "metrics.json"
