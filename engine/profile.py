"""Dataset profiling for the scout brief (rule R6 groundwork).

Deliberately lightweight: shapes, dtypes, missingness, cardinality, duplicate
rows, train/test parity and a target readout. The goal is a brief a coding
agent can act on — not an automated EDA report.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

# Files bigger than this are profiled on a sample so the cycle never stalls.
SAMPLE_ROWS = 500_000
BIG_FILE_BYTES = 1_500_000_000

ID_NAMES = {"id", "ids", "rowid", "row_id", "index", "customerid", "customer_id",
            "patientid", "patient_id", "sampleid", "sample_id"}

TARGET_CANDIDATES = ("target", "label", "class", "y", "outcome",
                     "heart disease", "churn", "irrigation_need")


def read_any(path: Path) -> tuple[pd.DataFrame, bool]:
    """Read a CSV, parquet or zip-adjacent file; return (frame, sampled)."""
    sampled = path.stat().st_size > BIG_FILE_BYTES
    if path.suffix.lower() == ".parquet":
        return pd.read_parquet(path), False
    if sampled:
        return pd.read_csv(path, nrows=SAMPLE_ROWS), True
    return pd.read_csv(path), False


def profile_frame(name: str, df: pd.DataFrame, sampled: bool = False) -> dict[str, Any]:
    columns = []
    for col in df.columns:
        series = df[col]
        columns.append({
            "name": str(col),
            "dtype": str(series.dtype),
            "missing_pct": round(100.0 * float(series.isna().mean()), 3),
            "nunique": int(series.nunique(dropna=True)),
            "sample": [str(v) for v in series.dropna().unique()[:3]],
        })
    return {
        "file": name,
        "rows": int(len(df)),
        "cols": int(df.shape[1]),
        "sampled": sampled,
        "duplicate_rows": int(df.duplicated().sum()),
        "memory_mb": round(float(df.memory_usage(deep=True).sum()) / 1e6, 1),
        "columns": columns,
    }


def detect_id_columns(columns: list[str]) -> list[str]:
    return [c for c in columns if c.strip().lower() in ID_NAMES]


def detect_target(train_columns: list[str], sub_columns: list[str] | None,
                  declared: str | None = None) -> str | None:
    """Target = declared name, else the train column absent from the submission
    template (the classic Kaggle layout), else a name heuristic."""
    if declared and declared in train_columns:
        return declared
    ids = set(detect_id_columns(train_columns))
    if sub_columns:
        missing = [c for c in train_columns if c not in sub_columns and c not in ids]
        if len(missing) == 1:
            return missing[0]
    lowered = {c.lower(): c for c in train_columns if c not in ids}
    for candidate in TARGET_CANDIDATES:
        if candidate in lowered:
            return lowered[candidate]
    return None


def compare_train_test(train: pd.DataFrame, test: pd.DataFrame,
                       target: str | None = None) -> dict[str, Any]:
    train_cols = [c for c in train.columns if c != target]
    test_cols = list(test.columns)
    shared = [c for c in train_cols if c in test_cols]
    only_train = [c for c in train_cols if c not in test_cols]
    only_test = [c for c in test_cols if c not in train_cols]

    id_overlap = None
    ids = detect_id_columns(test_cols)
    if ids:
        id_col = ids[0]
        try:
            id_overlap = int(len(set(train[id_col]) & set(test[id_col])))
        except KeyError:
            pass

    drift: dict[str, float] = {}
    for col in shared:
        if pd.api.types.is_numeric_dtype(train[col]) and pd.api.types.is_numeric_dtype(test[col]):
            a, b = train[col].dropna(), test[col].dropna()
            if len(a) and len(b) and a.std() > 0:
                ratio = abs(float(b.mean()) - float(a.mean())) / float(a.std())
                if ratio > 0.5:
                    drift[col] = round(ratio, 3)

    return {
        "shared_cols": len(shared),
        "only_train": only_train,
        "only_test": only_test,
        "id_column_overlap": id_overlap,
        "numeric_drift": dict(sorted(drift.items(), key=lambda kv: -kv[1])[:15]),
    }


def target_readout(df: pd.DataFrame, target: str) -> dict[str, Any]:
    y = df[target]
    out: dict[str, Any] = {
        "dtype": str(y.dtype),
        "missing": int(y.isna().sum()),
        "nunique": int(y.nunique(dropna=True)),
    }
    if y.nunique(dropna=True) <= 30 and not pd.api.types.is_float_dtype(y):
        vc = y.value_counts(dropna=True).head(30)
        out["distribution"] = {str(k): int(v) for k, v in vc.items()}
        counts = vc.to_numpy()
        out["imbalance_ratio"] = round(float(counts.max() / max(counts.min(), 1)), 2)
    elif pd.api.types.is_numeric_dtype(y):
        out["describe"] = {
            "mean": round(float(y.mean()), 5),
            "std": round(float(y.std()), 5),
            "min": round(float(y.min()), 5),
            "max": round(float(y.max()), 5),
        }
    return out


def profile_datasets_dir(datasets_dir: Path, target: str | None = None) -> list[dict[str, Any]]:
    profiles: list[dict[str, Any]] = []
    for path in sorted(datasets_dir.glob("*.csv")):
        try:
            df, sampled = read_any(path)
        except Exception as exc:  # noqa: BLE001 - a broken file must not kill the cycle
            profiles.append({"file": path.name, "error": str(exc)})
            continue
        prof = profile_frame(path.name, df, sampled)
        if target and target in df.columns and "train" in path.stem.lower():
            prof["target"] = target_readout(df, target)
        profiles.append(prof)
    return profiles


def render_markdown(profiles: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for prof in profiles:
        lines.append(f"### {prof.get('file', '?')}")
        lines.append("")
        if "error" in prof:
            lines.append(f"*(failed to profile: {prof['error']})*")
            lines.append("")
            continue
        note = " _(profiled on a sample)_" if prof.get("sampled") else ""
        lines.append(f"* {prof['rows']:,} rows x {prof['cols']:,} columns{note}; "
                     f"{prof.get('duplicate_rows', 0):,} duplicate rows; "
                     f"{prof.get('memory_mb', 0):,} MB")
        lines.append("")
        lines.append("| column | dtype | missing % | unique | samples |")
        lines.append("| --- | --- | --- | --- | --- |")
        for col in prof.get("columns", [])[:40]:
            lines.append(f"| {col['name']} | {col['dtype']} | {col['missing_pct']} | "
                         f"{col['nunique']} | {', '.join(col['sample'])} |")
        if len(prof.get("columns", [])) > 40:
            lines.append(f"| … | ({len(prof['columns']) - 40} more columns) | | | |")
        if "target" in prof:
            t = prof["target"]
            lines.append("")
            lines.append(f"**Target readout** — dtype `{t['dtype']}`, {t['nunique']} unique values"
                         + (f", imbalance ratio {t['imbalance_ratio']}" if "imbalance_ratio" in t else "")
                         + (f", distribution `{t['distribution']}`" if "distribution" in t else "")
                         + (f", describe `{t['describe']}`" if "describe" in t else ""))
        lines.append("")
    return "\n".join(lines)


def summarize(profiles: list[dict[str, Any]]) -> str:
    """One-paragraph summary for the coder prompt."""
    parts = []
    for prof in profiles:
        if "error" in prof:
            parts.append(f"{prof.get('file')}: unreadable")
            continue
        parts.append(f"{prof['file']}: {prof['rows']}x{prof['cols']}")
    return "; ".join(parts) if parts else "no CSVs profiled yet"
