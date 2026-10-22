"""Synthetic fictional supplier fleet for demos and tests.

All supplier and model names below are invented for this project -- none
represent a real manufacturer, model, or any proprietary sales data. The
lineup is deliberately spread across the credit/debit spectrum (an
EV-heavy brand, an ICE ute/truck brand, hybrids, a small EV challenger, a
premium ICE brand) so a demo run of `nves-au demo` produces a believable
mix of winners and losers in the league table, the way the real NVES
Regulator's first performance report did.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from nves_au.engine.models import VehicleRecord


@dataclass(frozen=True)
class ModelSpec:
    supplier: str
    model_name: str
    adr_category: str
    miro_kg: float
    base_co2_g_km: float  # CO2 in the first demo year; may improve slightly year over year
    base_units_sold: int  # typical annual volume, before random variation
    body_on_frame: bool = False
    braked_tow_rating_kg: float = 0
    annual_co2_improvement: float = 0.0  # fractional reduction per year (fleet efficiency trend)


# A deliberately varied fictional lineup: EV-first, ICE ute/truck, hybrid,
# premium ICE, small EV challenger, light-commercial ICE.
DEMO_MODEL_LINEUP: list[ModelSpec] = [
    # Dragonfly Motors -- EV-only passenger brand, should sit deep in credit.
    ModelSpec("Dragonfly Motors", "Dragonfly Comet", "MA", 1650, 0, 3200),
    ModelSpec("Dragonfly Motors", "Dragonfly Nova", "MA", 1800, 0, 2100),
    ModelSpec("Dragonfly Motors", "Dragonfly Horizon", "MC", 2100, 0, 1400),
    # Ironclad Trucks -- ICE utes/wagons/vans, should sit deep in debit.
    ModelSpec(
        "Ironclad Trucks", "Ironclad Ridge 4x4", "NA", 2250, 240, 4200,
        annual_co2_improvement=0.02,
    ),
    ModelSpec(
        "Ironclad Trucks", "Ironclad Summit", "MC", 2600, 260, 1800,
        body_on_frame=True, braked_tow_rating_kg=3500, annual_co2_improvement=0.015,
    ),
    ModelSpec(
        "Ironclad Trucks", "Ironclad Hauler Van", "NB1", 2100, 225, 1500,
        annual_co2_improvement=0.02,
    ),
    # Starling Auto -- mixed ICE/hybrid passenger brand, roughly mid-pack.
    ModelSpec(
        "Starling Auto", "Starling Breeze", "MA", 1300, 135, 3600,
        annual_co2_improvement=0.03,
    ),
    ModelSpec(
        "Starling Auto", "Starling Breeze Hybrid", "MA", 1400, 95, 2200,
        annual_co2_improvement=0.02,
    ),
    ModelSpec(
        "Starling Auto", "Starling Trail", "MC", 1900, 150, 1900,
        annual_co2_improvement=0.025,
    ),
    # Sapphire Motors -- premium ICE sedans/wagons, typically in debit.
    ModelSpec(
        "Sapphire Motors", "Sapphire GT", "MA", 1850, 185, 1300,
        annual_co2_improvement=0.015,
    ),
    ModelSpec(
        "Sapphire Motors", "Sapphire Odyssey", "MB", 2000, 200, 800,
        annual_co2_improvement=0.015,
    ),
    # Lotus Leaf EV -- small-volume EV challenger brand.
    ModelSpec("Lotus Leaf EV", "Leaf Pico", "MA", 1200, 0, 450),
    # Granite Commercial -- light-commercial ICE brand, typically in debit.
    ModelSpec(
        "Granite Commercial", "Granite Workhorse", "NA", 2200, 220, 2600,
        annual_co2_improvement=0.02,
    ),
    ModelSpec(
        "Granite Commercial", "Granite CityVan", "NB1", 1900, 195, 1700,
        annual_co2_improvement=0.02,
    ),
]


def generate_demo_fleet(
    years: list[int] | tuple[int, ...] = (2025,),
    seed: int = 42,
    volume_variation: float = 0.25,
) -> list[VehicleRecord]:
    """Build a reproducible synthetic fleet across the given performance years.

    units_sold varies randomly (+/- `volume_variation`) around each model's
    base volume, year over year, using a seeded RNG so the same `years` and
    `seed` always produce the same demo data. CO2 improves slowly each year
    for models with a non-zero `annual_co2_improvement`, simulating ordinary
    mid-cycle efficiency updates (EVs stay at 0 g/km throughout).
    """
    rng = random.Random(seed)
    records: list[VehicleRecord] = []
    base_year = min(years)

    for year in sorted(years):
        years_elapsed = year - base_year
        for spec in DEMO_MODEL_LINEUP:
            co2 = spec.base_co2_g_km * (1 - spec.annual_co2_improvement) ** years_elapsed
            variation = 1 + rng.uniform(-volume_variation, volume_variation)
            units_sold = max(1, round(spec.base_units_sold * variation))
            records.append(
                VehicleRecord(
                    supplier=spec.supplier,
                    model_name=spec.model_name,
                    performance_year=year,
                    adr_category=spec.adr_category,
                    body_on_frame=spec.body_on_frame,
                    braked_tow_rating_kg=spec.braked_tow_rating_kg,
                    miro_kg=spec.miro_kg,
                    co2_g_km=round(co2, 1),
                    units_sold=units_sold,
                )
            )
    return records
