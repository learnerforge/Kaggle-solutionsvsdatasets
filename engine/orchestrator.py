"""The cycle orchestrator: scout → code → execute → score → iterate → report.

This is the piece that runs every 24 hours (locally or in GitHub Actions).

Design rules encoded here:

* the coder is triggered when the notebook is missing, or again after every
  attempt that fails the score gate (R5/R7);
* structural check failures are fed back before score-based suggestions,
  because a notebook that does not run cannot have a score;
* at most ``ENGINE_MAX_ATTEMPTS`` coder attempts per cycle (R8);
* every attempt leaves a store row, a prompt file, a transcript and a report —
  a number with no artifact is not a result (R4/R13).
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from . import notebook_runner, opencode_runner, prompts, report as report_mod, scorer, scout as scout_mod, store, templates, validate
from .settings import Settings, load


@dataclass
class CycleOutcome:
    slug: str
    status: str                   # solved | not_reached | error | dry_run | no_work | blocked | scaffolded
    attempts: int = 0
    report: dict | None = None
    checks: dict | None = None
    notes: list[str] = field(default_factory=list)
    log: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return asdict(self)


def _log(outcome: CycleOutcome, message: str) -> None:
    stamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
    outcome.log.append(f"[{stamp}] {message}")
    # live stream on stderr: the CLI prints the human/JSON payload on stdout,
    # so echoing the log there as well would duplicate every cycle line
    print(f"[{stamp}] {message}", file=sys.stderr, flush=True)


def ensure_scaffold(slug: str, *, title: str | None = None, target: str | None = None,
                    metric: str | None = None, target_score: float | None = None,
                    force: bool = False, settings: Settings | None = None) -> dict[str, Path]:
    settings = settings or load()
    paths = templates.scaffold(
        settings.competition_dir(slug), slug, title=title, target=target,
        metric=metric, target_score=target_score, force=force,
    )
    store.register_competition(slug, title=title, metric=metric, target_score=target_score,
                               settings=settings)
    return paths


def run_coder_attempt(slug: str, *, brief: dict | None, attempt: int, feedback: str | None,
                      message: str | None = None, settings: Settings | None = None,
                      dry_run: bool = False) -> dict:
    """One coder turn. Returns a dict with the transcript and the store run id."""
    settings = settings or load()
    train_dir = settings.train_dir(slug)
    train_dir.mkdir(parents=True, exist_ok=True)

    prompt_text = message or prompts.coder_task_prompt(
        slug, brief, attempt, feedback=feedback,
        brief_path=settings.competition_dir(slug) / "BRIEF.md", settings=settings,
    )
    prompt_path = train_dir / f"prompt_attempt{attempt}.md"
    prompt_path.write_text(prompt_text, encoding="utf-8")

    run_id = store.start_run(slug, attempt, phase="code", settings=settings)
    if dry_run:
        _ = opencode_runner  # keep the import intentional and visible
        store.finish_run(run_id, "dry_run", notes="dry-run: opencode not invoked", settings=settings)
        return {"run_id": run_id, "dry_run": True, "prompt_path": prompt_path,
                "text": None, "session_id": None, "log_path": None}

    result = opencode_runner.run(
        f"Execute the attached task for competition `{slug}` (attempt {attempt}). "
        f"Work only inside competition/{slug}/.",
        slug=slug, attempt=attempt, prompt_path=prompt_path, settings=settings,
        title=f"{slug} attempt {attempt}",
    )
    status = "done" if result.ok else "failed"
    notes = result.error or "coder turn completed"
    store.finish_run(run_id, status, session_id=result.session_id,
                     log_path=str(result.log_path) if result.log_path else None,
                     notes=notes, settings=settings)
    return {
        "run_id": run_id, "dry_run": False, "prompt_path": prompt_path,
        "text": result.text, "session_id": result.session_id,
        "log_path": result.log_path, "ok": result.ok, "error": result.error,
    }


def run_cycle(slug: str | None = None, *, download: bool = True, refresh: bool = False,
              do_code: bool = True, do_execute: bool = True, force_code: bool = False,
              max_attempts: int | None = None, target_score: float | None = None,
              title: str | None = None, metric: str | None = None,
              target: str | None = None, dry_run: bool = False,
              wait_join: int = 0,
              settings: Settings | None = None) -> CycleOutcome:
    settings = settings or load()
    max_attempts = max_attempts or settings.max_attempts

    slug = slug or scout_mod.pick_daily(settings)
    if not slug:
        return CycleOutcome(slug="", status="no_work",
                            notes=["no competition selected: pass --slug or add one with init"])

    outcome = CycleOutcome(slug=slug, status="error")
    _log(outcome, f"cycle start for `{slug}` (dry_run={dry_run})")

    # --- 1/2. scaffold + scout ---------------------------------------------
    ensure_scaffold(slug, title=title, target=target, metric=metric,
                    target_score=target_score, settings=settings)
    brief_obj = scout_mod.scout(slug, download=download, refresh=refresh, title=title,
                                target=target, metric=metric, target_score=target_score,
                                wait_join=wait_join, settings=settings)
    brief = brief_obj.as_dict()
    for warning in brief_obj.warnings:
        _log(outcome, f"warning: {warning}")
    _log(outcome, f"scout: metric={brief_obj.metric} target={brief_obj.target} "
                  f"files={len(brief_obj.files)} profiles={len(brief_obj.profiles)}")

    if dry_run:
        for attempt in range(1, max_attempts + 1):
            run = run_coder_attempt(slug, brief=brief, attempt=attempt, feedback=None,
                                    settings=settings, dry_run=True)
            _log(outcome, f"attempt {attempt}: prompt written to {run['prompt_path']}")
        outcome.status = "dry_run"
        outcome.attempts = max_attempts
        report_mod.write_dashboard(settings)
        return outcome

    # --- guard: never burn coder attempts without data ----------------------
    # A notebook that cannot read ../datasets/ can only fail, so the cycle
    # stops here with an actionable message instead of producing a failed run.
    datasets_dir = settings.datasets_dir(slug)
    has_data = (any(datasets_dir.glob("*.csv")) or any(datasets_dir.glob("*.parquet"))
                or any(datasets_dir.glob("*.json")) or any(datasets_dir.glob("*.txt")))
    if do_execute and not has_data:
        outcome.status = "blocked"
        _log(outcome, f"blocked: no datasets under competition/{slug}/datasets/")
        _log(outcome, "the rules must be accepted in the browser first (no CLI "
                      "equivalent): https://www.kaggle.com/competitions/" + slug)
        _log(outcome, "re-run afterwards, or pass --wait N to let the cycle poll for the join")
        report_mod.write_dashboard(settings)
        return outcome

    # --- 3..6. code -> execute -> score -> iterate --------------------------
    feedback: str | None = None
    coder_message: str | None = None
    last_report: scorer.ScoreReport | None = None
    for attempt in range(1, max_attempts + 1):
        outcome.attempts = attempt
        notebook_exists = settings.code_path(slug).is_file()

        if do_code and (not notebook_exists or force_code or attempt > 1):
            _log(outcome, f"attempt {attempt}: triggering OpenCode coder")
            run = run_coder_attempt(slug, brief=brief, attempt=attempt, feedback=feedback,
                                    settings=settings)
            coder_message = run.get("text") or coder_message
            if run.get("error"):
                _log(outcome, f"attempt {attempt}: coder reported: {run['error']}")
            feedback = None  # consumed
        else:
            _log(outcome, f"attempt {attempt}: notebook present, skipping coder (baseline measurement)")

        if not do_execute:
            outcome.status = "scaffolded"
            break

        _log(outcome, f"attempt {attempt}: executing notebook")
        run_id = store.start_run(slug, attempt, phase="train", settings=settings)
        nb_result = notebook_runner.execute(slug, settings=settings)
        checks = validate.run_all(slug, settings=settings, artifacts_expected=True)
        (settings.train_dir(slug) / "checks.json").write_text(
            json.dumps(checks, indent=2), encoding="utf-8")
        outcome.checks = checks

        if not nb_result.ok:
            _log(outcome, f"attempt {attempt}: notebook FAILED ({nb_result.error[:160]}...)")
            store.finish_run(run_id, "failed",
                             notes=(nb_result.error or "execution failed")[:900], settings=settings)
            feedback = scorer.build_feedback(
                scorer.ScoreReport(slug=slug), checks=checks,
                execution_error=nb_result.error, settings=settings,
            )
            report_mod.write_attempt_report(
                slug, attempt=attempt, checks=checks, report=None, feedback=feedback,
                coder_message=coder_message, execution_error=nb_result.error, settings=settings)
            continue

        score_report = scorer.evaluate(slug, target_score=target_score, fetch_lb=True,
                                       settings=settings)
        last_report = score_report
        outcome.report = score_report.as_dict()
        _log(outcome, f"attempt {attempt}: {score_report.summary()}")

        store.finish_run(
            run_id, "done", cv_mean=score_report.cv_mean, cv_std=score_report.cv_std,
            lb_score=score_report.lb_score, score_reached=score_report.reached,
            notes=f"metric={score_report.metric}", settings=settings,
        )
        report_mod.write_attempt_report(
            slug, attempt=attempt, checks=checks, report=score_report, feedback=None,
            coder_message=coder_message, execution_error=None, settings=settings)

        if score_report.reached:
            outcome.status = "solved"
            store.set_status(slug, "solved", settings)
            _log(outcome, "gate reached — competition marked solved")
            if settings.submit_enabled:
                result = scorer.maybe_submit(slug, message=f"engine attempt {attempt}",
                                             settings=settings)
                _log(outcome, f"submit: {result}")
            break

        feedback = scorer.build_feedback(score_report, checks=checks, settings=settings)
        _log(outcome, f"gate not reached; feedback prepared for attempt {attempt + 1}")
    else:
        outcome.status = "not_reached"
        _log(outcome, f"stopped after {max_attempts} attempts without reaching the gate")
        store.set_status(slug, "in_progress", settings)

    if outcome.status == "not_reached" and last_report is not None:
        report_mod.write_attempt_report(
            slug, attempt=outcome.attempts, checks=outcome.checks, report=last_report,
            feedback=feedback, coder_message=coder_message, execution_error=None,
            settings=settings)

    # --- 7. report + sync ---------------------------------------------------
    report_mod.write_dashboard(settings)
    try:
        from . import vercel_sync

        if settings.vercel_sync_url:
            sync = vercel_sync.push(settings)
            _log(outcome, f"vercel sync: {sync}")
    except Exception as exc:  # noqa: BLE001 - sync never breaks a cycle
        _log(outcome, f"vercel sync skipped: {exc}")

    _log(outcome, f"cycle finished: {outcome.status}")
    return outcome


def run_ask(slug: str, question: str, *, settings: Settings | None = None,
            dry_run: bool = False) -> dict:
    """Hold a conversation with the coder about the competition sources."""
    settings = settings or load()
    brief = prompts.load_brief(slug, settings)
    prompt_text = prompts.ask_prompt(slug, question, brief,
                                     brief_path=settings.competition_dir(slug) / "BRIEF.md")
    train_dir = settings.train_dir(slug)
    train_dir.mkdir(parents=True, exist_ok=True)
    question_path = train_dir / "ask_last.md"
    question_path.write_text(prompt_text, encoding="utf-8")

    if dry_run:
        return {"dry_run": True, "prompt_path": question_path, "answer": None}

    result = opencode_runner.run(
        f"Answer the question in the attached file about competition `{slug}`.",
        slug=slug, attempt=0, prompt_path=question_path, settings=settings,
        title=f"{slug} question",
    )
    run_id = store.start_run(slug, 0, phase="ask", settings=settings)
    store.finish_run(run_id, "done" if result.ok else "failed",
                     session_id=result.session_id,
                     log_path=str(result.log_path) if result.log_path else None,
                     notes=question[:500], settings=settings)
    return {"dry_run": False, "prompt_path": question_path, "answer": result.text,
            "session_id": result.session_id, "ok": result.ok, "error": result.error,
            "log_path": result.log_path}
