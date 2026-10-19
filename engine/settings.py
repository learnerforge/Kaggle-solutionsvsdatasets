"""Central configuration for the engine.

Resolution order for every setting: environment variable > repo ``.env`` >
default. Credentials are never resolved here — see :mod:`engine.secrets`.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


def repo_root() -> Path:
    """Walk up from this file until a ``.git`` directory is found."""
    here = Path(__file__).resolve().parent
    for candidate in (here, *here.parents):
        if (candidate / ".git").exists():
            return candidate
    return here.parent


ROOT = repo_root()

# Load the repo-root .env if python-dotenv is installed. Failure is non-fatal:
# plain environment variables still work.
try:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
except Exception:  # pragma: no cover - dotenv optional at import time
    pass


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, ""))
    except ValueError:
        return default


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_float(name: str) -> float | None:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return None
    try:
        return float(raw)
    except ValueError:
        return None


@dataclass(frozen=True)
class Settings:
    repo_root: Path
    competitions_root: Path
    state_dir: Path          # .engine/ — SQLite DB, scratch, caches (git-ignored)
    frontend_data: Path      # frontend/data — dashboard.json consumed by frontend/

    # --- opencode coder -----------------------------------------------------
    opencode_model: str | None      # e.g. "anthropic/claude-sonnet-4"; None = default
    opencode_agent: str | None      # e.g. "build"; None = default agent
    opencode_timeout: int           # seconds for one opencode run
    opencode_standalone: bool       # private server instead of shared background service

    # --- pipeline -----------------------------------------------------------
    max_attempts: int                # coder attempts per cycle before giving up
    notebook_timeout: int            # seconds for one notebook execution
    submit_enabled: bool             # R9: engine only submits when explicitly allowed
    default_target_score: float | None
    default_higher_is_better: bool

    # --- kaggle credentials -------------------------------------------------
    # "local"  -> KAGGLE_USERNAME/KAGGLE_KEY env or ~/.kaggle/kaggle.json
    # "remote" -> fetched over HTTPS from a private endpoint (future Vercel DB).
    #             Off by default; storing Kaggle secrets in a shared DB is a
    #             deliberate last resort (see engine/secrets.py).
    kaggle_source: str
    kaggle_remote_url: str | None
    kaggle_remote_token: str | None

    # --- optional Vercel sync (non-secret data only) ------------------------
    vercel_sync_url: str | None
    vercel_sync_token: str | None

    # extra tries after a transient coder failure (exit != 0 / empty response)
    opencode_retries: int = 1

    def competition_dir(self, slug: str) -> Path:
        return self.competitions_root / slug

    @property
    def db_path(self) -> Path:
        """SQLite run history lives in the git-ignored .engine/ state dir."""
        return self.state_dir / "engine.db"

    def code_path(self, slug: str) -> Path:
        return self.competition_dir(slug) / "code" / f"{slug}.ipynb"

    def datasets_dir(self, slug: str) -> Path:
        return self.competition_dir(slug) / "datasets"

    def train_dir(self, slug: str) -> Path:
        return self.competition_dir(slug) / "train"


@lru_cache(maxsize=1)
def load() -> Settings:
    root = ROOT
    return Settings(
        repo_root=root,
        competitions_root=root / "competition",
        state_dir=root / ".engine",
        frontend_data=root / "frontend" / "data",
        opencode_model=os.environ.get("ENGINE_OPENCODE_MODEL") or None,
        opencode_agent=os.environ.get("ENGINE_OPENCODE_AGENT") or None,
        opencode_timeout=_env_int("ENGINE_OPENCODE_TIMEOUT", 3600),
        opencode_standalone=_env_flag("ENGINE_OPENCODE_STANDALONE", default=bool(os.environ.get("CI"))),
        max_attempts=_env_int("ENGINE_MAX_ATTEMPTS", 3),
        notebook_timeout=_env_int("ENGINE_NOTEBOOK_TIMEOUT", 3600),
        submit_enabled=_env_flag("ENGINE_SUBMIT_ENABLED", False),
        default_target_score=_env_float("ENGINE_TARGET_SCORE"),
        default_higher_is_better=_env_flag("ENGINE_HIGHER_IS_BETTER", True),
        kaggle_source=os.environ.get("ENGINE_KAGGLE_SOURCE", "local").strip().lower(),
        kaggle_remote_url=os.environ.get("ENGINE_KAGGLE_REMOTE_URL") or None,
        kaggle_remote_token=os.environ.get("ENGINE_KAGGLE_REMOTE_TOKEN") or None,
        vercel_sync_url=os.environ.get("VERCEL_SYNC_URL") or None,
        vercel_sync_token=os.environ.get("VERCEL_SYNC_TOKEN") or None,
        opencode_retries=_env_int("ENGINE_OPENCODE_RETRIES", 1),
    )
