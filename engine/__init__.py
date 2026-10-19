"""Kaggle Solutions vs Datasets — the engine.

The engine runs two agents and one pipeline:

* **Scout** (``engine/scout.py``) — stays alive to the Kaggle competition:
  pulls the problem statement, evaluation metric, file list and a dataset
  profile before any code is written, so the coder never codes blind.
* **Coder** (``engine/opencode_runner.py``) — OpenCode itself, triggered on
  every attempt, writing ``competition/<slug>/code/<slug>.ipynb`` under the
  rules in ``engine/rules.py`` and answering questions about the sources.
* **Pipeline** (``engine/orchestrator.py``) — scout -> code -> execute ->
  score-gate -> iterate, with every number recorded in a local SQLite store
  (``engine/store.py``) and surfaced through ``frontend/``.

Legacy rule R10: the engine never reads, writes or references the ``NTG/``
trial-and-error folder.
"""

__version__ = "0.1.0"
