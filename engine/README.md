# engine/ — the Kaggle solution engine

Two agents and one pipeline:

| Agent | Module | Job |
| --- | --- | --- |
| **Scout** | `scout.py` (+ `kaggle_client.py`, `profile.py`) | Stays alive to the competition: problem statement, evaluation page, file list, datasets, schema/target profile. Writes `PROBLEM_STATEMENT.md`, `BRIEF.md`, `train/brief.json`. |
| **Coder** | `opencode_runner.py` (+ `prompts.py`, `rules.py`) | OpenCode itself, triggered per attempt. Writes/repairs `competition/<slug>/code/<slug>.pynb` under the rulebook and answers questions about the sources (`engine ask`). |
| **Pipeline** | `orchestrator.py` (+ `templates.py`, `notebook_runner.py`, `validate.py`, `scorer.py`, `report.py`) | scout → code → execute → score gate → iterate → report. State in SQLite (`store.py`), projection to the frontend, optional Vercel sync (`vercel_sync.py`). |

## Commands

```text
python -m engine list                    # competitions and state
python -m engine status                  # cycle stats, recent runs, sync status
python -m engine init <slug> [--title T] [--target C] [--metric M] [--target-score S]
python -m engine scout <slug> [--no-download] [--refresh]
python -m engine prompt <slug> [--attempt N]     # print the coder prompt
python -m engine code <slug> [--attempt N] [--dry-run]
python -m engine train <slug> [--timeout S]      # execute the notebook
python -m engine score <slug> [--target-score S] [--fetch-lb]
python -m engine verify <slug> [--artifacts]     # requirement checks
python -m engine report [slug]                   # refresh frontend/data/dashboard.json
python -m engine cycle [<slug>] [--dry-run] [--no-code] [--no-train] [--force-code]
python -m engine ask <slug> "question"
python -m engine submit <slug> [--message M]     # requires ENGINE_SUBMIT_ENABLED=1
python -m engine rules                           # print the rulebook
python -m engine sync [push|pull|status]         # Vercel projection
```

All commands accept `--json`.

## The loop

1. `ensure_scaffold` enforces the folder contract (R1) and materialises a
   runnable baseline notebook if the code folder is empty.
2. `scout` gathers sources and profiles the data; **no code is written before
   the sources are understood**.
3. The coder is triggered whenever the notebook is missing, and again after
   every attempt that misses the gate. The prompt = rulebook + brief + last
   feedback (ordered by the R7 ladder).
4. `notebook_runner` executes the notebook top-to-bottom with the notebook's own
   folder as cwd, so `../datasets/` and `../train/` resolve exactly as they do
   locally. Failures keep a partial executed copy — that is the next
   attempt's debugging context.
5. `scorer` reads `train/metrics.json` (the only source of truth, R4), compares
   against the gate (R5), and emits ladder-ordered feedback.
6. `report` writes `train/report.md` and `frontend/data/dashboard.json`;
   `vercel_sync` pushes the projection if an endpoint is configured.

## Environment variables

See `.env.example`. The important ones:

| Variable | Meaning | Default |
| --- | --- | --- |
| `KAGGLE_USERNAME` / `KAGGLE_KEY` | Kaggle CLI credentials | `~/.kaggle/kaggle.json` fallback |
| `ENGINE_MAX_ATTEMPTS` | coder attempts per cycle | `3` |
| `ENGINE_NOTEBOOK_TIMEOUT` | seconds per notebook execution | `3600` |
| `ENGINE_OPENCODE_TIMEOUT` | seconds per coder turn | `3600` |
| `ENGINE_OPENCODE_MODEL` / `ENGINE_OPENCODE_AGENT` | what to trigger | OpenCode defaults |
| `ENGINE_SUBMIT_ENABLED` | allow real Kaggle submissions (R9) | `0` |
| `ENGINE_TARGET_SCORE` | default gate | unset (per-competition wins) |
| `VERCEL_SYNC_URL` / `VERCEL_SYNC_TOKEN` | dashboard projection endpoint | unset |

## Security notes (R12)

* Credentials are resolved in `secrets.py` — env first, then
  `~/.kaggle/kaggle.json`, then (opt-in only) an HTTPS endpoint. They are never
  printed (`repr` is redacted), never passed on a command line, never synced.
* The Vercel projection carries scores, checks and metadata only. If a remote
  credential source is ever used, it should be Vercel Environment Variables
  behind a dedicated endpoint — not rows in a shared database.
* `validate.py` scans notebooks/readmes for credential-like patterns and fails
  R12 if anything matches, or if `datasets/`/`train/` contents are tracked by git.

## Self-test

The pipeline can be tested end-to-end without Kaggle: scaffold a throwaway
slug, generate small synthetic CSVs (train/test/sample_submission), then run
`python -m engine cycle <slug> --no-download --no-code` — the baseline notebook
executes, writes `metrics.json`, and the gate/checks run for real.

## Legacy folder

`NTG/` is a historical trial-and-error workspace. The engine never reads,
writes or references it (R10); it is git-ignored as well.
