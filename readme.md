# Kaggle Solutions vs Datasets

An engine that solves Kaggle competitions end-to-end and makes every claim it
makes **traceable**: one agent stays permanently briefed on each competition's
sources (problem statement, evaluation metric, datasets), OpenCode writes the
solution notebook every time it is triggered, a versioned rulebook constrains
what "done" means, and a score gate decides when a competition counts as
solved — never an invented number, never a dropped problem statement.

---

## Contents

- [The promise: nothing is lost](#the-promise-nothing-is-lost)
- [Repository layout](#repository-layout)
- [Quickstart](#quickstart)
- [The two agents](#the-two-agents)
- [The rulebook (R1–R13)](#the-rulebook-r1r13)
- [Score matching](#score-matching)
- [The 24-hour cycle](#the-24-hour-cycle)
- [Security and credentials](#security-and-credentials)
- [The Vercel database (optional, pluggable)](#the-vercel-database-optional-pluggable)
- [The frontend dashboard](#the-frontend-dashboard)
- [Demo competition walkthrough](#demo-competition-walkthrough)
- [Troubleshooting](#troubleshooting)
- [Development notes](#development-notes)
- [Roadmap](#roadmap)

---

## The promise: nothing is lost

Three mechanisms enforce it:

1. **Artifact trail (R4/R13).** Every executed attempt leaves `train/metrics.json`,
   out-of-fold predictions, feature importance, a submission file, the executed
   notebook copy and a transcript of the coding agent. A number that is not in an
   artifact does not exist.
2. **Run history.** Every attempt — coder turns, executions, score evaluations,
   submissions — is a row in a local SQLite store (`.engine/engine.db`,
   git-ignored) and surfaces in `train/report.md` and the dashboard.
3. **Datasets are re-downloadable, not committable.** Kaggle data lands in
   `competition/<slug>/datasets/` via the Kaggle CLI and is excluded from git by
   construction, so the repo stays small while `engine scout` restores any
   competition at any time.

---

## Repository layout

```text
Kaggle-solutionsvsdatasets/
├── engine/                       <- the agent pipeline (python -m engine …)
│   ├── rules.py                  <- rulebook R1–R13, versioned, prompt-injected
│   ├── scout.py                  <- agent #1: problem statement + dataset profile
│   ├── kaggle_client.py          <- Kaggle CLI 2.x wrapper (JSON output modes)
│   ├── profile.py                <- schema / missingness / parity / target readout
│   ├── prompts.py                <- coder task + "ask" prompt builders
│   ├── opencode_runner.py        <- agent #2: headless `opencode run` per attempt
│   ├── notebook_runner.py        <- executes code/<slug>.pynb, keeps artifacts
│   ├── templates.py              <- baseline notebook + README + folder scaffold
│   ├── validate.py               <- requirement checks with evidence (frontend)
│   ├── scorer.py                 <- score gate + ladder-ordered feedback
│   ├── report.py                 <- train/report.md + frontend/data/dashboard.json
│   ├── vercel_sync.py            <- optional non-secret dashboard projection
│   ├── store.py                  <- SQLite: competitions, runs, submissions
│   ├── orchestrator.py           <- scout → code → train → score → iterate
│   └── cli.py                    <- one verb set for every operation
├── frontend/                     <- static dashboard (index / competitions /
│                                    requirements / rules + data/dashboard.json)
├── competition/
│   └── <slug>/
│       ├── code/<slug>.pynb      <- the ONLY source artifact (R1)
│       ├── datasets/             <- Kaggle CLI download — git-ignored
│       ├── train/                <- metrics, submission, oof, reports — git-ignored
│       ├── PROBLEM_STATEMENT.md  <- fetched from Kaggle by the scout
│       ├── BRIEF.md              <- statement + files + dataset profile
│       └── readme.md             <- algorithm walkthrough + score matching (R11)
├── .github/workflows/daily-cycle.yml   <- the 24h clock
├── .env.example                  <- every engine variable, documented
└── .engine/                      <- local state (SQLite) — git-ignored
```

The legacy `NTG/` folder is a historical trial-and-error workspace: it is
git-ignored and the engine never reads, writes or references it (R10).

---

## Quickstart

```powershell
# 0. environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m ipykernel install --user --name python3

# 1. credentials (either/or — never both, never committed)
#    a) kaggle auth login          (writes ~/.kaggle/kaggle.json)
#    b) copy .env.example -> .env and fill KAGGLE_USERNAME / KAGGLE_KEY
# 2. install the coder
npm install -g opencode-ai

# 3. join the competition in the browser (rules acceptance is per-competition)

# 4. scaffold + scout + measure + iterate
python -m engine init playground-series-s6e2 --title "Predicting Heart Disease" --metric roc_auc
python -m engine scout playground-series-s6e2
python -m engine cycle playground-series-s6e2

# 5. inspect
python -m engine score playground-series-s6e2 --fetch-lb
python -m engine verify playground-series-s6e2 --artifacts
python -m engine status
```

`python -m engine cycle <slug> --dry-run` shows exactly what would happen
(scout + the full coder prompt) without invoking OpenCode or training anything.

---

## The two agents

**Agent 1 — Scout** (`engine/scout.py`). Permanently briefed on the competition:
it pulls the problem statement, evaluation and rules pages through the Kaggle
CLI (`--format json`), lists the files, downloads the datasets into
`competition/<slug>/datasets/`, and profiles every CSV (shape, dtypes,
missingness, cardinality, duplicates, train/test parity, numeric drift, target
distribution). It writes `PROBLEM_STATEMENT.md` and `BRIEF.md` — and every coder
prompt is built from that brief, so code is never written blind.

**Agent 2 — Coder** (`engine/opencode_runner.py`). OpenCode, triggered headlessly
(`opencode run --format json --auto --file <prompt>`). It receives: the full
rulebook, the brief, the deliverable contract, and the feedback from the previous
attempt. It writes `code/<slug>.pynb` and keeps `readme.md` honest. Its final
message ("what I changed, what I measured, what I need next") is stored as the
communication record for that attempt. `python -m engine ask <slug> "question"`
opens the same channel for questions about the competition sources.

---

## The rulebook (R1–R13)

Versioned (`engine/rules.py`), injected into every coder prompt, and audited per
competition by `engine verify`. Full text: `python -m engine rules` or the
[rulebook page](frontend/rules.html).

| Rule | Requirement |
| --- | --- |
| R1 | Folder contract: `code/<slug>.pynb` is the only source artifact; `datasets/` read-only; `train/` for outputs; `readme.md` the write-up |
| R2 | One notebook, runs top-to-bottom on a fresh machine, no manual steps |
| R3 | Determinism: one `SEED` seeds every library |
| R4 | Honest measurement: OOF-only scores, `train/metrics.json` every run |
| R5 | Score matching gate: solved only when the measured OOF score meets the target; diagnose the CV-vs-LB gap before adding models |
| R6 | Leakage discipline: fold-safe encodings, OOF completeness asserted |
| R7 | Optimization ladder: baseline → folds → features → model zoo → OOF ensemble → target encoding → pseudo-labels → bounded search |
| R8 | Resource budget: CPU, notebook timeout, bounded attempts per cycle |
| R9 | Submission policy: only through the engine, only when `ENGINE_SUBMIT_ENABLED=1`, always logged |
| R10 | The legacy `NTG/` folder does not exist — never read, written or referenced |
| R11 | README write-up: problem, algorithm, score table from artifacts, rejected ideas, next steps |
| R12 | Security: no credentials in code, notebooks, logs or the database; no data in git |
| R13 | Reproducible artifacts: every attempt leaves its evidence behind |

A failed structural check always outranks a bad score: a notebook that cannot
run is not a solution, so the feedback loop repairs structure first.

---

## Score matching

The gate decides when a competition counts as solved:

```text
train/metrics.json  ──►  scorer.evaluate()  ──►  cv_mean  vs  target_score
        ▲                                            │
        │                                   reached? ─┴─ yes → status "solved"
        │                                            │ no
        └──── next attempt, ladder feedback ◄────────┘
```

* The target comes from `--target-score` (stored per competition) or
  `ENGINE_TARGET_SCORE`; direction is inferred from the metric (RMSE/MAE/log-loss
  are lower-is-better).
* The **CV-vs-leaderboard gap** is the diagnostic that matters. A large negative
  gap means the validation split is unrepresentative — duplicates, group leakage
  or distribution shift — and the feedback says to fix that *before* adding models.
* Feedback is ordered by the R7 ladder and cites real numbers: fold variance,
  which model families are missing, whether an ensemble exists, whether target
  encoding was fold-safe.
* Nothing is submitted to Kaggle unless `ENGINE_SUBMIT_ENABLED=1`, and every
  submission is logged (R9).

---

## The 24-hour cycle

Every 24 hours one problem statement is picked and driven to a measured result.

**Locally:**

```powershell
# single unit of work
python -m engine cycle                # picks the next unsolved competition
python -m engine cycle playground-series-s6e2

# as a long-running 24h loop (Windows Task Scheduler can call this instead)
while ($true) { python -m engine cycle; Start-Sleep -Seconds 86400 }
```

**In CI:** `.github/workflows/daily-cycle.yml` runs on a daily cron
(`17 3 * * *`) plus `workflow_dispatch` (with an optional slug and dry-run).
It installs Python + Node + OpenCode, runs the cycle, uploads the `train/`
artifacts (datasets excluded), refreshes the dashboard and commits the
competition sources and `frontend/data/dashboard.json` back to the repo.

CI secrets/variables:

| Kind | Name | Purpose |
| --- | --- | --- |
| secret | `KAGGLE_USERNAME`, `KAGGLE_KEY` | Kaggle API access |
| secret | `<PROVIDER>_API_KEY` | the coder's model key (e.g. `ANTHROPIC_API_KEY`) |
| var | `DAILY_SLUG` | pin one competition (default: next unsolved) |
| var | `ENGINE_SUBMIT_ENABLED` | `1` allows real submissions |
| var | `ENGINE_MAX_ATTEMPTS`, `ENGINE_OPENCODE_MODEL` | budget and model |

Note: Kaggle rule acceptance is per-competition and per-account — the engine
cannot join competitions for you, it surfaces the 403 with that instruction.

---

## Security and credentials

* **Resolution order** (`engine/secrets.py`): `KAGGLE_USERNAME`/`KAGGLE_KEY`
  env → `~/.kaggle/kaggle.json` → (opt-in) an HTTPS endpoint. Credentials are
  redacted in every `repr`/log, injected into the Kaggle CLI's environment
  (never written to a file by the engine, never on a command line).
* **Never in git:** `kaggle.json`, `.env*`, key files — plus every dataset,
  submission and model artifact (`.gitignore`).
* **Audited:** `engine verify` fails R12 if a credential-like pattern appears
  in a notebook or README, or if `datasets/`/`train/` contents are tracked.
* **The coder is not trusted with secrets:** prompts contain competition facts,
  not credentials; the runner passes the provider key only via the process
  environment that OpenCode already uses.
* The legacy `NTG/` folder is off-limits to the engine (R10) and to git.

---

## The Vercel database (optional, pluggable)

No database is required to run the engine today: state lives in
`.engine/engine.db` (SQLite) and the frontend reads a JSON file. When a Vercel
database is added later, the contract is already implemented in
`engine/vercel_sync.py`:

* **push** — `POST` the dashboard projection (competitions, OOF/LB scores,
  requirement checks, rulebook version) to `VERCEL_SYNC_URL` with a bearer
  token; a serverless function writes it to Postgres/KV.
* **pull** — `GET …?action=queue` returns a prioritised list of slugs (optional).
* **never synced** — Kaggle credentials, dataset contents, local paths. If a
  remote credential source is ever wanted, it is an HTTPS endpoint backed by
  Vercel *Environment Variables* (encrypted at rest, per-deployment scoped),
  read only when `ENGINE_KAGGLE_SOURCE=remote` — deliberately not rows in a
  shared database, where a dump would leak the account.

---

## The frontend dashboard

Static, no build step (`frontend/`):

| Page | Shows |
| --- | --- |
| `index.html` | cycle stats, engine configuration, the 7-step pipeline, last run |
| `competitions.html` | per-competition cards: OOF ± std, gate, LB, gap, attempts, checks, links; recent run table |
| `requirements.html` | the R1–R13 × competitions matrix with per-cell evidence |
| `rules.html` | the rulebook, the optimization ladder, the security model |

Data source: `frontend/data/dashboard.json`, written by
`python -m engine report` (and by the daily CI cycle). Serve locally with any
static server, e.g. `python -m http.server -d frontend`.

**Live:** <https://kaggle-solutions-dashboard.vercel.app> — deployed with the
Vercel CLI from the repo root. `vercel.json` pins `outputDirectory: frontend`
and `framework: null`, and `.vercelignore` excludes everything except the
dashboard (Vercel does **not** read `.gitignore`, so the engine, the
`NTG/` legacy folder and all competition data are explicitly blocked from ever
uploading). Redeploy after `python -m engine report` with:

```powershell
vercel deploy --prod --yes
```

---

## Demo competition walkthrough

`competition/playground-series-s6e2/` (Playground Series S6E2 — Predicting
Heart Disease) is scaffolded and ready:

```powershell
# 1. join the competition in the browser first
python -m engine scout playground-series-s6e2        # statement + datasets + profile
python -m engine cycle playground-series-s6e2        # code -> train -> score -> iterate
python -m engine score playground-series-s6e2 --fetch-lb
```

The starter notebook (`code/playground-series-s6e2.pynb`) is a leak-free
LightGBM baseline: auto target detection, stratified 5-fold CV, OOF metric,
fold-averaged test predictions, `metrics.json` + `submission.csv` + OOF and
importance artifacts. The coder extends it from there. Set the gate once you
know your target:

```powershell
python -m engine init playground-series-s6e2 --target-score 0.90
```

Then `readme.md` section 3 fills itself from `train/metrics.json` via the score
table — never by hand (R4/R11).

---

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| `403 Forbidden` on scout/download | Competition rules not accepted for your account | Join in the browser and accept the rules; the API token alone is not sufficient |
| `No Kaggle credentials found` | No env vars, no `~/.kaggle/kaggle.json` | `kaggle auth login` or fill `.env` (see `.env.example`) |
| `nbclient missing` / `No module named 'ipykernel'` | Notebook execution stack not installed | `pip install -r requirements.txt` and `python -m ipykernel install --user --name python3` |
| Notebook fails in the load cell | Datasets not downloaded yet | `python -m engine scout <slug>` (it downloads into `datasets/`) |
| `opencode CLI not found on PATH` | Coder not installed | `npm install -g opencode-ai` |
| Gate never reached, CV noisy | Fold variance / unrepresentative split | Feedback says step 2 first: more folds, then check duplicates and grouping (R5/R7) |
| `metrics.json` missing after a run | Notebook does not honour the artifact contract | `engine verify` shows R4 failing; the next coder prompt receives that as feedback |
| Frontend shows "could not load dashboard.json" | `file://` fetch or stale dashboard | `python -m engine report`, then serve `frontend/` over HTTP |
| Score moved between runs | Library drift in boosting stacks | Record `pip freeze` next to `train/metrics.json`; seeds are already fixed (R3) |

---

## Development notes

* **Add a rule:** edit `RULES` in `engine/rules.py` (version bump), and add a
  matching check in `engine/validate.py` if it can be audited mechanically —
  the frontend matrix picks it up automatically.
* **Self-test without Kaggle:** scaffold a throwaway slug, drop small synthetic
  CSVs into its `datasets/`, then
  `python -m engine cycle <slug> --no-download --no-code` executes the full
  train → score → verify path.
* **Adding the Vercel backend:** implement one serverless endpoint that accepts
  the dashboard JSON and optionally returns `{"queue": [...]}`; nothing in the
  engine changes.
* **Prompt inspection:** `python -m engine prompt <slug> --attempt 2` prints the
  exact message the coder would receive — prompts are never hidden state.

---

## Roadmap

- [ ] Attach the Vercel Postgres/KV backend and serve the dashboard from it.
- [ ] Leaderboard-derived default gates (median of the public LB) via
      `engine scout --fetch-lb`.
- [ ] Pseudo-labelling and OOF-ensemble stages promoted from coder freedom into
      audited pipeline steps.
- [ ] Submission quota awareness per competition (daily limits) in the store.
- [ ] Per-competition GPU quota handling for the big-kernel competitions.

---

## License & contributions

One competition per folder, named with the exact Kaggle slug. No hard-coded
columns outside the competition folder. No target-dependent transform before a
split. Every reported number must exist in an artifact.
