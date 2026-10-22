"""CSV <-> VehicleRecord conversion, shared by the CLI, Streamlit app and
the synthetic data generator.

Expected CSV columns (header row required):
    supplier, model_name, performance_year, adr_category, body_on_frame,
    braked_tow_rating_kg, miro_kg, co2_g_km, units_sold

body_on_frame and braked_tow_rating_kg are optional (default False / 0) --
only needed for MC vehicles near the Type 2 reclassification threshold.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from nves_au.engine.models import VehicleRecord

CSV_COLUMNS = [
    "supplier",
    "model_name",
    "performance_year",
    "adr_category",
    "body_on_frame",
    "braked_tow_rating_kg",
    "miro_kg",
    "co2_g_km",
    "units_sold",
]


def vehicle_records_to_dataframe(records: list[VehicleRecord]) -> pd.DataFrame:
    return pd.DataFrame([r.model_dump() for r in records], columns=CSV_COLUMNS)


def write_fleet_csv(records: list[VehicleRecord], path: str | Path) -> None:
    vehicle_records_to_dataframe(records).to_csv(path, index=False)


def dataframe_to_vehicle_records(df: pd.DataFrame) -> list[VehicleRecord]:
    missing = set(CSV_COLUMNS) - set(df.columns)
    # body_on_frame / braked_tow_rating_kg are optional with sensible defaults.
    missing -= {"body_on_frame", "braked_tow_rating_kg"}
    if missing:
        raise ValueError(f"Fleet data is missing required column(s): {sorted(missing)}")

    has_body_on_frame = "body_on_frame" in df.columns
    has_tow_rating = "braked_tow_rating_kg" in df.columns

    records = []
    for _, row in df.iterrows():
        body_on_frame = bool(row["body_on_frame"]) if has_body_on_frame else False
        tow_rating = float(row["braked_tow_rating_kg"] or 0) if has_tow_rating else 0
        records.append(
            VehicleRecord(
                supplier=str(row["supplier"]),
                model_name=str(row["model_name"]),
                performance_year=int(row["performance_year"]),
                adr_category=str(row["adr_category"]),
                body_on_frame=body_on_frame,
                braked_tow_rating_kg=tow_rating,
                miro_kg=float(row["miro_kg"]),
                co2_g_km=float(row["co2_g_km"]),
                units_sold=int(row["units_sold"]),
            )
        )
    return records


def read_fleet_csv(path: str | Path) -> list[VehicleRecord]:
    # keep_default_na=False: pandas otherwise treats the literal ADR category
    # code "NA" (light commercial) as a missing value, which it is not.
    df = pd.read_csv(path, keep_default_na=False)
    return dataframe_to_vehicle_records(df)
