"""Scenario simulator: apply "what if" sales-mix changes to a baseline fleet
and compare the resulting credit position and penalty risk.

A scenario file (YAML) lists adjustments against a baseline fleet:

    name: "Shift 500 units from the Ridge 4x4 to the Comet"
    adjustments:
      - supplier: Ironclad Trucks
        model_name: Ironclad Ridge 4x4
        performance_year: 2025
        delta_units: -500
      - supplier: Dragonfly Motors
        model_name: Dragonfly Comet
        performance_year: 2025
        delta_units: 500

An adjustment that matches an existing (supplier, model_name,
performance_year) line changes its units_sold by delta_units (removing the
line if that reaches exactly zero; raising an error if it would go
negative). An adjustment with no match and a positive delta_units
introduces a brand-new model line -- for that, adr_category, miro_kg and
co2_g_km must also be given.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from nves_au.config import RegulationConfig
from nves_au.engine.aggregate import aggregate_by_supplier_year
from nves_au.engine.ledger import PeriodOutcome, run_ledger
from nves_au.engine.models import VehicleRecord
from nves_au.engine.targets import score_fleet


@dataclass(frozen=True)
class ScenarioAdjustment:
    supplier: str
    model_name: str
    performance_year: int
    delta_units: int
    # Only required when the adjustment introduces a brand-new model line.
    adr_category: str | None = None
    miro_kg: float | None = None
    co2_g_km: float | None = None
    body_on_frame: bool = False
    braked_tow_rating_kg: float = 0


def load_scenario(path: str | Path) -> tuple[str, list[ScenarioAdjustment]]:
    with Path(path).open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    name = data.get("name", Path(path).stem)
    adjustments = [ScenarioAdjustment(**a) for a in data.get("adjustments", [])]
    return name, adjustments


def apply_scenario(
    baseline: list[VehicleRecord], adjustments: list[ScenarioAdjustment]
) -> list[VehicleRecord]:
    records = list(baseline)
    for adj in adjustments:
        matches = [
            i
            for i, r in enumerate(records)
            if r.supplier == adj.supplier
            and r.model_name == adj.model_name
            and r.performance_year == adj.performance_year
        ]
        if len(matches) > 1:
            raise ValueError(
                f"Scenario adjustment for {adj.supplier}/{adj.model_name}/"
                f"{adj.performance_year} matches {len(matches)} baseline lines; "
                "expected exactly one."
            )

        if matches:
            i = matches[0]
            existing = records[i]
            new_units = existing.units_sold + adj.delta_units
            if new_units < 0:
                raise ValueError(
                    f"Adjustment would make units_sold negative for "
                    f"{adj.supplier}/{adj.model_name}/{adj.performance_year} "
                    f"({existing.units_sold} + {adj.delta_units})"
                )
            if new_units == 0:
                records.pop(i)
            else:
                records[i] = existing.model_copy(update={"units_sold": new_units})
            continue

        if adj.delta_units <= 0:
            raise ValueError(
                f"No baseline line found for {adj.supplier}/{adj.model_name}/"
                f"{adj.performance_year} to reduce; for a new model, delta_units "
                "must be positive."
            )
        missing = [
            field_name
            for field_name in ("adr_category", "miro_kg", "co2_g_km")
            if getattr(adj, field_name) is None
        ]
        if missing:
            raise ValueError(
                f"New model line {adj.supplier}/{adj.model_name}/{adj.performance_year} "
                f"needs {missing} supplied in the scenario adjustment."
            )
        records.append(
            VehicleRecord(
                supplier=adj.supplier,
                model_name=adj.model_name,
                performance_year=adj.performance_year,
                adr_category=adj.adr_category,
                body_on_frame=adj.body_on_frame,
                braked_tow_rating_kg=adj.braked_tow_rating_kg,
                miro_kg=adj.miro_kg,
                co2_g_km=adj.co2_g_km,
                units_sold=adj.delta_units,
            )
        )
    return records


@dataclass(frozen=True)
class ScenarioComparison:
    name: str
    baseline_outcomes: list[PeriodOutcome]
    scenario_outcomes: list[PeriodOutcome]

    def by_supplier_year(self) -> dict[tuple[str, int], tuple[PeriodOutcome, PeriodOutcome]]:
        """Pairs each (supplier, year) baseline outcome with its scenario
        counterpart, for suppliers/years present in both."""
        baseline_map = {(o.supplier, o.performance_year): o for o in self.baseline_outcomes}
        scenario_map = {(o.supplier, o.performance_year): o for o in self.scenario_outcomes}
        keys = sorted(set(baseline_map) & set(scenario_map))
        return {key: (baseline_map[key], scenario_map[key]) for key in keys}


def run_scenario(
    baseline: list[VehicleRecord],
    adjustments: list[ScenarioAdjustment],
    config: RegulationConfig,
    name: str = "scenario",
) -> ScenarioComparison:
    scenario_fleet = apply_scenario(baseline, adjustments)

    baseline_positions = aggregate_by_supplier_year(score_fleet(baseline, config))
    scenario_positions = aggregate_by_supplier_year(score_fleet(scenario_fleet, config))

    _, baseline_outcomes = run_ledger(baseline_positions, config)
    _, scenario_outcomes = run_ledger(scenario_positions, config)

    return ScenarioComparison(
        name=name, baseline_outcomes=baseline_outcomes, scenario_outcomes=scenario_outcomes
    )
