"""Loader for Green Vehicle Guide (GVG) model CO2/mass reference data.

Source: Green Vehicle Guide, Australian Government (Department of
Infrastructure, Transport, Regional Development, Communications and the
Arts) -- https://www.greenvehicleguide.gov.au/

NO CONFIRMED BULK DOWNLOAD OR API: this project's research pass (web search
only; direct fetches to the GVG site were blocked by this session's network
policy, see config/regulation/README.md) found a per-search and per-vehicle
CSV export button on the GVG site, but no documented bulk dataset or API.
Retrieved 2026-10-22. Re-check the site directly before assuming this is
still the only option.

Manual download steps (do this yourself, then point this loader at the file):
  1. Go to https://www.greenvehicleguide.gov.au/
  2. Use "Compare Vehicles" / "Search" to find the models you need (filter by
     make, model, year, etc.), or open an individual vehicle's page.
  3. Click the CSV export icon on the results page (or the vehicle page's
     "Download as ... CSV" link).
  4. Save the file and pass its path to `load_gvg_export()` below.

The exact column headers in that export were NOT confirmed during this
research pass (one secondary source suggested a vehicle-mass column exists
but didn't state its header text or units, and whether it reflects the MIRO
figure the NVES mass-adjustment formula needs is itself unconfirmed -- see
the `caveats` note on this module). `column_map` lets you adapt to whatever
headers your actual export has, and the loader fails loudly (rather than
guessing) if none of the candidate headers for a required field are found.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

# Candidate header names for each field we need, in priority order. These
# are best-effort guesses (not confirmed against a real export) -- override
# with your own column_map if your file's headers differ.
DEFAULT_COLUMN_MAP: dict[str, list[str]] = {
    "model_name": ["Model", "Variant", "Vehicle", "Vehicle Description"],
    "co2_g_km": ["CO2 (g/km)", "CO2", "CO2 Combined (g/km)", "CO2 Emissions (g/km)"],
    "mass_kg": ["Mass (kg)", "Tare Mass (kg)", "Mass", "Weight (kg)"],
}

CAVEATS = (
    "The Green Vehicle Guide's mass field (if present in your export) has not "
    "been confirmed to be Mass In Running Order (MIRO) as defined by the NVES "
    "Act -- it may be tare mass, kerb mass, or another figure. Cross-check a "
    "few rows against the vehicle's compliance plate / manufacturer "
    "specifications before feeding mass_kg into the NVES target formula."
)


class GreenVehicleGuideError(Exception):
    pass


def _resolve_column(columns: list[str], candidates: list[str]) -> str | None:
    for candidate in candidates:
        if candidate in columns:
            return candidate
    return None


def load_gvg_export(
    path: str | Path, column_map: dict[str, list[str]] | None = None
) -> pd.DataFrame:
    """Load a manually-downloaded GVG CSV export and normalise its columns
    to {model_name, co2_g_km, mass_kg}.

    Raises GreenVehicleGuideError (listing the columns actually found) if a
    required field can't be matched -- pass your own `column_map` to adapt.
    """
    column_map = column_map or DEFAULT_COLUMN_MAP
    raw = pd.read_csv(path, keep_default_na=False)

    resolved: dict[str, str] = {}
    missing: list[str] = []
    for field, candidates in column_map.items():
        column = _resolve_column(list(raw.columns), candidates)
        if column is None:
            missing.append(field)
        else:
            resolved[field] = column

    if missing:
        raise GreenVehicleGuideError(
            f"Could not find a column for {missing} in {path}. "
            f"Columns found: {list(raw.columns)}. Pass column_map= with your "
            "export's actual headers."
        )

    normalised = raw.rename(columns={source: field for field, source in resolved.items()})
    return normalised[list(resolved.keys())]
