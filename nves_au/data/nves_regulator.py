"""Loader for the NVES Regulator's published supplier-level performance
report (per-entity interim emissions values and unit holdings).

Source: NVES Regulator, Australian Government --
https://www.nvesregulator.gov.au/reporting-and-data

NO CONFIRMED BULK/API ENDPOINT: this project's research pass (web search
only; direct fetches to nvesregulator.gov.au were blocked by this session's
network policy, see config/regulation/README.md) found that the Regulator
publishes performance results per reporting period (e.g. "2025 NVES
performance period results") on that page, and separately lists NVES unit
holdings per registry account, but did not confirm the exact file format
(CSV/XLSX/HTML table) or a stable download URL. Retrieved 2026-10-22.

Manual download steps (do this yourself, then point this loader at the file):
  1. Go to https://www.nvesregulator.gov.au/reporting-and-data
  2. Open the performance period or unit-holdings report you want.
  3. Download the published table in whatever format the Regulator
     currently offers (export it to CSV first if it's only shown as an
     HTML table or PDF).
  4. Save the file and pass its path to `load_regulator_performance_report()`
     below.

Column headers were NOT confirmed during this research pass -- adapt
`column_map` to your actual file.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

DEFAULT_COLUMN_MAP: dict[str, list[str]] = {
    "supplier": ["Entity", "Regulated entity", "Supplier", "Entity name"],
    "performance_year": ["Performance period", "Performance year", "Year"],
    "iev_units": ["IEV", "Interim emissions value", "IEV (units)"],
    "units_issued": ["Units issued", "NVES units issued", "Units"],
}


class NvesRegulatorDataError(Exception):
    pass


def _resolve_column(columns: list[str], candidates: list[str]) -> str | None:
    for candidate in candidates:
        if candidate in columns:
            return candidate
    return None


def load_regulator_performance_report(
    path: str | Path, column_map: dict[str, list[str]] | None = None
) -> pd.DataFrame:
    """Load a manually-downloaded NVES Regulator performance report and
    normalise its columns to {supplier, performance_year, iev_units,
    units_issued} (whichever of those fields are present in the file --
    `units_issued` is optional since not every report includes it).
    """
    column_map = column_map or DEFAULT_COLUMN_MAP
    raw = pd.read_csv(path, keep_default_na=False)

    resolved: dict[str, str] = {}
    missing: list[str] = []
    for field, candidates in column_map.items():
        column = _resolve_column(list(raw.columns), candidates)
        if column is None:
            if field != "units_issued":  # optional field
                missing.append(field)
        else:
            resolved[field] = column

    if missing:
        raise NvesRegulatorDataError(
            f"Could not find a column for {missing} in {path}. "
            f"Columns found: {list(raw.columns)}. Pass column_map= with your "
            "report's actual headers."
        )

    normalised = raw.rename(columns={source: field for field, source in resolved.items()})
    return normalised[list(resolved.keys())]
