"""Command line for the engine: ``python -m engine <command>``.

One verb set for the whole lifecycle:

    list      what competitions exist locally and what state they are in
    status    cycle statistics and the last runs
    init      create the folder contract + baseline notebook + README
    scout     fetch problem statement, files, datasets and profile them
    prompt    print the exact prompt the coder would receive (no OpenCode call)
    code      trigger OpenCode to write/repair the notebook
    train     execute the notebook and keep the artifacts
    score     read metrics.json and compare against the score gate
    verify    run the rulebook checks and show the requirement matrix
    report    write run reports and refresh the frontend dashboard
    cycle     scout -> code -> train -> score -> iterate (the 24h unit of work)
    ask       ask the coder a question about the competition sources
    submit    submit a finished submission (only if ENGINE_SUBMIT_ENABLED=1)
    rules     print the rulebook
    sync      push/pull the dashboard to a Vercel database endpoint
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from . import notebook_runner, orchestrator, prompts, report as report_mod, rules, scorer, scout as scout_mod, store, validate, vercel_sync
from .settings import load


def _emit(payload: Any, as_json: bool, human: str | None = None) -> int:
    if as_json:
        print(json.dumps(payload, indent=2, default=str))
    else:
        print(human if human is not None else json.dumps(payload, indent=2, default=str))
    return 0


# --------------------------------------------------------------------------- #
# commands
# --------------------------------------------------------------------------- #

def cmd_list(args: argparse.Namespace) -> int:
    settings = load()
    known = {c["slug"]: c for c in store.list_competitions(settings)}
    on_disk = sorted(p.name for p in settings.competitions_root.iterdir()
                     if p.is_dir()) if settings.competitions_root.is_dir() else []

    rows = []
    for slug in sorted(set(known) | set(on_disk)):
        comp = known.get(slug, {})
        report = scorer.evaluate(slug, settings=settings)
        rows.append({
            "slug": slug,
            "title": comp.get("title") or slug,
            "status": comp.get("status", "on_disk"),
            "metric": report.metric,
            "cv_mean": report.cv_mean,
            "target_score": report.target_score,
            "reached": report.reached,
            "has_notebook": settings.code_path(slug).is_file(),
            "has_metrics": scorer.metrics_path(slug, settings).is_file(),
        })
    if args.json:
        return _emit(rows, True)
    if not rows:
        print("No competitions yet. Start with: python -m engine init <slug>")
        return 0
    print(f"{'slug':<34} {'status':<12} {'metric':<20} {'OOF':>10} {'gate':>10}  nb")
    for row in rows:
        oof = "-" if row["cv_mean"] is None else f"{row['cv_mean']:.5f}"
        gate = "-" if row["target_score"] is None else f"{row['target_score']:.5f}"
        print(f"{row['slug']:<34} {row['status']:<12} {str(row['metric'] or '-'):<20} "
              f"{oof:>10} {gate:>10}  {'yes' if row['has_notebook'] else 'no'}")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    settings = load()
    payload = {
        "stats": store.cycle_stats(settings),
        "recent_runs": store.recent_runs(10, settings),
        "sync": vercel_sync.status(settings),
    }
    return _emit(payload, args.json)


def cmd_init(args: argparse.Namespace) -> int:
    settings = load()
    paths = orchestrator.ensure_scaffold(
        args.slug, title=args.title, target=args.target, metric=args.metric,
        target_score=args.target_score, force=args.force, settings=settings,
    )
    payload = {key: str(value) for key, value in paths.items()}
    human = "\n".join([
        f"scaffolded competition/{args.slug}/",
        f"  notebook : {paths['code']}",
        f"  readme   : {paths['readme']}",
        f"  datasets : {paths['datasets']}  (git-ignored)",
        f"  train    : {paths['train']}  (git-ignored)",
        "",
        f"next: python -m engine scout --slug {args.slug}",
    ])
    return _emit(payload, args.json, human)


def cmd_scout(args: argparse.Namespace) -> int:
    settings = load()
    brief = scout_mod.scout(
        args.slug, download=not args.no_download, refresh=args.refresh,
        title=args.title, target=args.target, metric=args.metric,
        target_score=args.target_score, settings=settings,
    )
    human = "\n".join([
        f"scouted {brief.slug}",
        f"  metric      : {brief.metric} ({'higher' if brief.higher_is_better else 'lower'} is better)",
        f"  target      : {brief.target}",
        f"  files       : {len(brief.files)}",
        f"  profiles    : {len(brief.profiles)}",
        f"  brief       : competition/{brief.slug}/BRIEF.md",
        f"  statement   : competition/{brief.slug}/PROBLEM_STATEMENT.md",
    ] + ([f"  warnings    : {len(brief.warnings)}"] if brief.warnings else []))
    return _emit(brief.as_dict(), args.json, human)


def cmd_prompt(args: argparse.Namespace) -> int:
    settings = load()
    brief = prompts.load_brief(args.slug, settings)
    text = prompts.coder_task_prompt(args.slug, brief, args.attempt, brief_path=None,
                                     settings=settings)
    if args.json:
        return _emit({"slug": args.slug, "attempt": args.attempt, "prompt": text}, True)
    print(text)
    return 0


def cmd_code(args: argparse.Namespace) -> int:
    settings = load()
    brief = prompts.load_brief(args.slug, settings)
    result = orchestrator.run_coder_attempt(
        args.slug, brief=brief, attempt=args.attempt, feedback=None,
        settings=settings, dry_run=args.dry_run,
    )
    if args.json:
        return _emit({k: str(v) for k, v in result.items()}, True)
    print(f"prompt written : {result['prompt_path']}")
    if result.get("dry_run"):
        print("dry-run: opencode was not invoked")
    else:
        print(f"transcript     : {result.get('log_path')}")
        print(f"session        : {result.get('session_id')}")
        print(f"ok             : {result.get('ok')}")
        if result.get("error"):
            print(f"error          : {result['error']}")
        if result.get("text"):
            print("\n--- coder message ---\n")
            print(result["text"])
    return 0


def cmd_train(args: argparse.Namespace) -> int:
    settings = load()
    result = notebook_runner.execute(args.slug, settings=settings, timeout=args.timeout)
    payload = {
        "ok": result.ok,
        "duration_sec": round(result.duration_sec, 1),
        "executed_path": str(result.executed_path) if result.executed_path else None,
        "error": result.error,
    }
    human = "\n".join([
        f"{'OK' if result.ok else 'FAILED'} — {args.slug} ({result.duration_sec:.1f}s)",
        f"  executed copy : {result.executed_path}",
        *([f"  error         : {result.error[:500]}"] if result.error else []),
    ])
    return _emit(payload, args.json, human)


def cmd_score(args: argparse.Namespace) -> int:
    settings = load()
    report = scorer.evaluate(args.slug, target_score=args.target_score,
                             fetch_lb=args.fetch_lb, settings=settings)
    human = [report.summary()]
    human += [f"* {note}" for note in report.notes]
    if report.reached is False:
        human += ["", "## Next-attempt feedback", "", scorer.build_feedback(report, settings=settings)]
    return _emit(report.as_dict(), args.json, "\n".join(human))


def cmd_verify(args: argparse.Namespace) -> int:
    settings = load()
    checks = validate.run_all(args.slug, settings=settings, artifacts_expected=args.artifacts)
    if args.json:
        return _emit(checks, True)
    print(f"# Requirement checks — {args.slug}")
    print()
    print(f"{'rule':<5} {'status':<6} {'requirement':<34} evidence")
    for check in checks["checks"]:
        print(f"{check['rule']:<5} {check['status']:<6} {check['title']:<34} {check['detail']}")
    print()
    print("PASS" if checks["passed"] else f"FAILED rules: {', '.join(checks['failed'])}")
    return 0 if checks["passed"] else 1


def cmd_report(args: argparse.Namespace) -> int:
    settings = load()
    path = report_mod.write_dashboard(settings)
    payload = {"dashboard": str(path)}
    if args.slug:
        brief = scout_mod.scout(args.slug, download=False, settings=settings)
        payload["brief"] = brief.slug
    return _emit(payload, args.json, f"dashboard written: {path}")


def cmd_cycle(args: argparse.Namespace) -> int:
    settings = load()
    outcome = orchestrator.run_cycle(
        args.slug, download=not args.no_download, refresh=args.refresh,
        do_code=not args.no_code, do_execute=not args.no_train,
        force_code=args.force_code, max_attempts=args.max_attempts,
        target_score=args.target_score, title=args.title, metric=args.metric,
        target=args.target, dry_run=args.dry_run, settings=settings,
    )
    human = "\n".join(outcome.log + ["", f"result: {outcome.status}"])
    return _emit(outcome.as_dict(), args.json, human)


def cmd_ask(args: argparse.Namespace) -> int:
    settings = load()
    result = orchestrator.run_ask(args.slug, args.question, settings=settings,
                                  dry_run=args.dry_run)
    if args.json:
        return _emit({k: str(v) for k, v in result.items()}, True)
    if result.get("dry_run"):
        print(f"prompt written: {result['prompt_path']} (dry-run: opencode not invoked)")
        return 0
    print(result.get("answer") or result.get("error") or "(no answer)")
    return 0


def cmd_submit(args: argparse.Namespace) -> int:
    settings = load()
    result = scorer.maybe_submit(args.slug, message=args.message, settings=settings)
    return _emit(result, args.json, json.dumps(result, indent=2, default=str))


def cmd_rules(args: argparse.Namespace) -> int:
    if args.json:
        return _emit({
            "version": rules.RULEBOOK_VERSION,
            "rules": [{"id": r, "title": t, "text": x} for r, t, x in rules.RULES],
        }, True)
    print(rules.as_markdown())
    return 0


def cmd_sync(args: argparse.Namespace) -> int:
    settings = load()
    if args.action == "push":
        result = vercel_sync.push(settings)
    elif args.action == "pull":
        result = vercel_sync.pull(settings)
    else:
        result = vercel_sync.status(settings)
    return _emit(result, args.json, json.dumps(result, indent=2, default=str))


# --------------------------------------------------------------------------- #
# parser
# --------------------------------------------------------------------------- #

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m engine",
        description="Kaggle solutions engine: scout -> code (OpenCode) -> train -> score -> iterate.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    def add(name: str, help_text: str, func):
        p = sub.add_parser(name, help=help_text, description=help_text)
        p.add_argument("--json", action="store_true", help="machine-readable output")
        p.set_defaults(func=func)
        return p

    add("list", "List competitions and their state.", cmd_list)
    add("status", "Show cycle statistics and sync status.", cmd_status)

    p = add("init", "Create the folder contract for a competition.", cmd_init)
    p.add_argument("slug")
    p.add_argument("--title")
    p.add_argument("--target", help="target column name (else auto-detected)")
    p.add_argument("--metric", help="e.g. roc_auc, balanced_accuracy, rmse")
    p.add_argument("--target-score", type=float, dest="target_score",
                   help="score gate (rule R5)")
    p.add_argument("--force", action="store_true", help="overwrite notebook and readme")

    p = add("scout", "Fetch the problem statement, files, datasets and profile them.", cmd_scout)
    p.add_argument("slug")
    p.add_argument("--no-download", action="store_true")
    p.add_argument("--refresh", action="store_true", help="re-fetch Kaggle metadata")
    p.add_argument("--title")
    p.add_argument("--target")
    p.add_argument("--metric")
    p.add_argument("--target-score", type=float, dest="target_score")

    p = add("prompt", "Print the coder prompt for an attempt (no OpenCode call).", cmd_prompt)
    p.add_argument("slug")
    p.add_argument("--attempt", type=int, default=1)

    p = add("code", "Trigger OpenCode to write or repair the notebook.", cmd_code)
    p.add_argument("slug")
    p.add_argument("--attempt", type=int, default=1)
    p.add_argument("--dry-run", action="store_true")

    p = add("train", "Execute the notebook and keep the artifacts.", cmd_train)
    p.add_argument("slug")
    p.add_argument("--timeout", type=int, default=None, help="seconds (default ENGINE_NOTEBOOK_TIMEOUT)")

    p = add("score", "Compare the measured OOF score with the gate.", cmd_score)
    p.add_argument("slug")
    p.add_argument("--target-score", type=float, dest="target_score")
    p.add_argument("--fetch-lb", action="store_true", help="also query the leaderboard")

    p = add("verify", "Run the rulebook checks (requirement matrix).", cmd_verify)
    p.add_argument("slug")
    p.add_argument("--artifacts", action="store_true",
                   help="also require run artifacts (metrics.json, oof, executed copy)")

    p = add("report", "Write run reports and refresh the frontend dashboard.", cmd_report)
    p.add_argument("slug", nargs="?")

    p = add("cycle", "Run the full 24h unit of work.", cmd_cycle)
    p.add_argument("slug", nargs="?", help="omit to pick the next unsolved competition")
    p.add_argument("--no-download", action="store_true")
    p.add_argument("--refresh", action="store_true")
    p.add_argument("--no-code", action="store_true", help="skip OpenCode, only measure")
    p.add_argument("--no-train", action="store_true", help="scaffold/scout only")
    p.add_argument("--force-code", action="store_true", help="trigger the coder even if a notebook exists")
    p.add_argument("--max-attempts", type=int, default=None, dest="max_attempts")
    p.add_argument("--target-score", type=float, dest="target_score")
    p.add_argument("--title")
    p.add_argument("--metric")
    p.add_argument("--target")
    p.add_argument("--dry-run", action="store_true",
                   help="scout + write prompts, never invoke OpenCode or execute anything")

    p = add("ask", "Ask the coder a question about the competition sources.", cmd_ask)
    p.add_argument("slug")
    p.add_argument("question")
    p.add_argument("--dry-run", action="store_true")

    p = add("submit", "Submit train/submission.csv (requires ENGINE_SUBMIT_ENABLED=1).", cmd_submit)
    p.add_argument("slug")
    p.add_argument("--message", default="")

    add("rules", "Print the engine rulebook.", cmd_rules)

    p = add("sync", "Sync the dashboard with a Vercel database endpoint.", cmd_sync)
    p.add_argument("action", nargs="?", choices=["push", "pull", "status"], default="status")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args) or 0)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
