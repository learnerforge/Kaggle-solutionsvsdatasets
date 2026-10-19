"""Structural and hygiene checks mapped to the rulebook (R1–R13).

These run before and after a training attempt. They answer the question the
frontend asks: *which requirements of the problem statement are actually
satisfied, with evidence?* A failed structural check always outranks a bad
score — a notebook that cannot run is not a solution.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

from .settings import Settings, load

PASS, FAIL, WARN, NA = "pass", "fail", "warn", "n/a"

SECRET_PATTERNS = [
    re.compile(r"KAGGLE_KEY\s*[:=]\s*['\"][A-Za-z0-9]{16,}"),
    re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['\"][A-Za-z0-9_\-]{20,}"),
    re.compile(r"['\"]?key['\"]?\s*:\s*['\"][a-f0-9]{32}['\"]"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
]


@dataclass
class Check:
    rule: str
    title: str
    status: str
    detail: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


def _notebook_source(path: Path) -> str:
    import nbformat

    nb = nbformat.read(str(path), as_version=4)
    return "\n".join(cell.get("source", "") for cell in nb.cells if cell.cell_type == "code")


def _git_tracked(slug: str, settings: Settings) -> set[str]:
    """Files git tracks under the competition folder. Never inspects NTG/."""
    try:
        proc = subprocess.run(
            ["git", "ls-files", f"competition/{slug}"],
            cwd=str(settings.repo_root), capture_output=True, text=True, timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired):  # pragma: no cover
        return set()
    if proc.returncode != 0:
        return set()
    return {line.strip().replace("\\", "/") for line in proc.stdout.splitlines() if line.strip()}


def run_all(slug: str, *, settings: Settings | None = None,
            artifacts_expected: bool = False) -> dict:
    settings = settings or load()
    comp_dir = settings.competition_dir(slug)
    notebook = settings.code_path(slug)
    datasets_dir = settings.datasets_dir(slug)
    train_dir = settings.train_dir(slug)
    readme = comp_dir / "readme.md"
    checks: list[Check] = []

    # --- R1 folder contract -------------------------------------------------
    missing = [str(p.relative_to(comp_dir)) for p in (notebook, datasets_dir, train_dir, readme)
               if not p.exists()]
    checks.append(Check(
        "R1", "Folder contract", PASS if not missing else FAIL,
        "code/<slug>.pynb, datasets/, train/ and readme.md all present."
        if not missing else f"missing: {', '.join(missing)}",
    ))

    # --- R10 legacy folder --------------------------------------------------
    if notebook.is_file():
        source_all = notebook.read_text(encoding="utf-8", errors="replace")
        readme_text = readme.read_text(encoding="utf-8", errors="replace") if readme.is_file() else ""
        mentions = "NTG" in source_all or "NTG" in readme_text
        checks.append(Check(
            "R10", "Legacy folder untouched", FAIL if mentions else PASS,
            "no reference to the legacy workspace" if not mentions
            else "notebook or readme references NTG/ (rule R10 violation)",
        ))

    if not notebook.is_file():
        for rule, title in [("R2", "Notebook runs top-to-bottom"), ("R3", "Determinism"),
                            ("R6", "Leakage discipline"), ("R9", "Submission policy")]:
            checks.append(Check(rule, title, NA, "no notebook yet"))
        checks.append(Check("R11", "README write-up", WARN if readme.is_file() else FAIL,
                            "readme.md present but not yet populated" if readme.is_file()
                            else "readme.md missing"))
        return _summarize(slug, checks)

    try:
        import nbformat

        nb = nbformat.read(str(notebook), as_version=4)
        code_cells = [c for c in nb.cells if c.cell_type == "code"]
        source = _notebook_source(notebook)
        valid = True
    except Exception as exc:  # noqa: BLE001
        checks.append(Check("R2", "Notebook runs top-to-bottom", FAIL, f"unreadable notebook: {exc}"))
        return _summarize(slug, checks)

    checks.append(Check(
        "R2", "Notebook runs top-to-bottom", PASS if valid and len(code_cells) >= 5 else WARN,
        f"{len(code_cells)} code cells, valid nbformat v{nb.nbformat}",
    ))

    # --- R3 determinism -----------------------------------------------------
    has_seed = bool(re.search(r"^\s*SEED\s*=\s*\d+", source, re.M))
    seeds_libs = source.count("random_state=SEED") + source.count("seed_everything")
    checks.append(Check(
        "R3", "Determinism", PASS if has_seed and seeds_libs >= 2 else WARN,
        f"SEED constant={'yes' if has_seed else 'no'}, seeding calls={seeds_libs}",
    ))

    # --- R6 leakage discipline ----------------------------------------------
    fold_api = re.search(r"(StratifiedKFold|GroupKFold|TimeSeriesSplit|KFold)", source)
    oof_guard = bool(re.search(r"assert[^\n]*oof", source, re.I))
    checks.append(Check(
        "R6", "Leakage discipline", PASS if fold_api and oof_guard else WARN,
        f"folds={'yes' if fold_api else 'no'}, OOF completeness assert={'yes' if oof_guard else 'no'}",
    ))

    # --- R9 submission policy -----------------------------------------------
    upload = re.search(r"(kaggle\s+competitions\s+submit|competitions\.submit)", source)
    checks.append(Check(
        "R9", "No uploads from the notebook", FAIL if upload else PASS,
        "notebook never submits" if not upload else "notebook contains a submission call",
    ))

    # --- R12 security -------------------------------------------------------
    hits = [pattern.pattern for pattern in SECRET_PATTERNS if pattern.search(source)]
    if readme.is_file():
        readme_text = readme.read_text(encoding="utf-8", errors="replace")
        hits += [p.pattern for p in SECRET_PATTERNS if p.search(readme_text)]
    tracked = _git_tracked(slug, settings)
    leaked = sorted(f for f in tracked
                    if f.startswith(f"competition/{slug}/datasets/") and not f.endswith(".gitkeep")
                    or f.startswith(f"competition/{slug}/train/") and not f.endswith(".gitkeep"))
    if hits or leaked:
        detail = []
        if hits:
            detail.append(f"credential-like patterns: {hits}")
        if leaked:
            detail.append(f"data/artifacts tracked by git: {leaked[:5]}")
        checks.append(Check("R12", "Security and git hygiene", FAIL, "; ".join(detail)))
    else:
        checks.append(Check("R12", "Security and git hygiene", PASS,
                            "no credential patterns; no datasets or train artifacts tracked"))

    # --- R11 README write-up ------------------------------------------------
    if readme.is_file():
        text = readme.read_text(encoding="utf-8", errors="replace")
        sections = sum(1 for n in range(1, 6) if re.search(rf"^##\s*{n}\.", text, re.M))
        checks.append(Check("R11", "README write-up", PASS if sections >= 5 else WARN,
                            f"{sections}/5 required sections present (R11)"))
    else:
        checks.append(Check("R11", "README write-up", FAIL, "readme.md missing"))

    # --- R4/R13 artifacts ---------------------------------------------------
    if artifacts_expected:
        metrics = train_dir / "metrics.json"
        oof = list(train_dir.glob("oof_*.csv"))
        importance = list(train_dir.glob("importance_*.csv"))
        executed = list(train_dir.glob("*_executed.ipynb"))
        submission = train_dir / "submission.csv"
        missing_art = []
        if not metrics.is_file():
            missing_art.append("metrics.json")
        if not oof:
            missing_art.append("oof_*.csv")
        if not executed:
            missing_art.append("executed notebook copy")
        checks.append(Check(
            "R4", "Honest measurement", PASS if metrics.is_file() else FAIL,
            "train/metrics.json written" if metrics.is_file()
            else "train/metrics.json missing — score cannot be verified (R4)",
        ))
        checks.append(Check(
            "R13", "Reproducible artifacts", PASS if not missing_art else FAIL,
            f"oof files={len(oof)}, importance files={len(importance)}, "
            f"submission={'yes' if submission.is_file() else 'no'}, "
            f"executed copy={'yes' if executed else 'no'}"
            + (f"; missing: {missing_art}" if missing_art else ""),
        ))

    return _summarize(slug, checks)


def _summarize(slug: str, checks: list[Check]) -> dict:
    failed = [c.rule for c in checks if c.status == FAIL]
    warned = [c.rule for c in checks if c.status == WARN]
    return {
        "slug": slug,
        "checks": [c.as_dict() for c in checks],
        "failed": failed,
        "warned": warned,
        "passed": not failed,
    }
