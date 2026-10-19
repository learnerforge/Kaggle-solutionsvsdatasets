"""Execute a competition notebook and capture everything it wrote.

Uses ``nbclient`` (the same engine ``jupyter nbconvert --execute`` uses), with
the notebook's own directory as the working directory so that the relative
``../datasets/`` and ``../train/`` paths inside the notebook resolve exactly as
they do when a human runs it. A partially executed copy is preserved on failure
— that artifact is what the next attempt's feedback is built from.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

import nbformat

from .settings import Settings, load


@dataclass
class NotebookResult:
    ok: bool
    executed_path: Path | None
    duration_sec: float
    error: str | None = None
    error_cell: int | None = None


def _cell_error(nb: nbformat.NotebookNode) -> tuple[str | None, int | None]:
    for index, cell in enumerate(nb.cells):
        if cell.cell_type != "code":
            continue
        for output in cell.get("outputs", []):
            if output.get("output_type") == "error":
                tb = "\n".join(output.get("traceback", []))
                summary = f"{output.get('ename')}: {output.get('evalue')}"
                return f"{summary}\n{tb}", index
    return None, None


def execute(slug: str, *, settings: Settings | None = None,
            timeout: int | None = None, notebook_path: Path | None = None) -> NotebookResult:
    settings = settings or load()
    timeout = timeout or settings.notebook_timeout
    notebook_path = notebook_path or settings.code_path(slug)
    executed_dir = settings.train_dir(slug)
    executed_dir.mkdir(parents=True, exist_ok=True)
    executed_path = executed_dir / f"{slug}_executed.ipynb"

    if not notebook_path.is_file():
        return NotebookResult(False, None, 0.0, f"notebook not found: {notebook_path}")

    started = time.time()
    try:
        nb = nbformat.read(str(notebook_path), as_version=4)
    except Exception as exc:  # noqa: BLE001
        return NotebookResult(False, None, time.time() - started,
                              f"invalid notebook format: {exc}")

    try:
        from nbclient import NotebookClient
        from nbclient.exceptions import CellExecutionError
    except ImportError as exc:  # pragma: no cover
        return NotebookResult(False, None, time.time() - started,
                              f"nbclient missing ({exc}); install requirements.txt")

    client = NotebookClient(
        nb,
        timeout=timeout,
        kernel_name="python3",
        allow_errors=False,
        resources={"metadata": {"path": str(notebook_path.parent)}},
    )
    try:
        client.execute()
        ok, error, error_cell = True, None, None
    except CellExecutionError as exc:
        ok, error, error_cell = False, str(exc)[:6000], None
    except Exception as exc:  # noqa: BLE001 - kernel crash, timeout, etc.
        ok, error, error_cell = False, f"{type(exc).__name__}: {exc}"[:6000], None

    duration = time.time() - started
    try:
        nbformat.write(nb, str(executed_path))
    except Exception:  # noqa: BLE001 - keep the original error if writing fails
        executed_path = None

    if not ok and error_cell is None:
        error_cell = _cell_error(nb)[1]
    return NotebookResult(ok, executed_path, duration, error, error_cell)


def latest_stdout_lines(slug: str, *, settings: Settings | None = None,
                        limit: int = 40) -> list[str]:
    """Last lines of the notebook's stdout, for the run report."""
    settings = settings or load()
    executed_path = settings.train_dir(slug) / f"{slug}_executed.ipynb"
    if not executed_path.is_file():
        return []
    try:
        nb = nbformat.read(str(executed_path), as_version=4)
    except Exception:  # noqa: BLE001
        return []
    lines: list[str] = []
    for cell in nb.cells:
        if cell.cell_type != "code":
            continue
        for output in cell.get("outputs", []):
            if output.get("output_type") == "stream":
                lines.extend(str(output.get("text", "")).splitlines())
    return lines[-limit:]
