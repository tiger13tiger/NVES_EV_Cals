"""Per-vehicle classification, target and credit/debit calculation."""

from __future__ import annotations

from nves_au.config import RegulationConfig
from nves_au.engine.models import VehicleRecord, VehicleResult


def classify_and_score(record: VehicleRecord, config: RegulationConfig) -> VehicleResult:
    """Classify a vehicle, compute its mass-adjusted target, and its credit/debit.

    credit/debit sign convention: net_units < 0 means the vehicle line is a
    credit contribution (it beats its target); net_units > 0 is a debit
    contribution. This matches the Regulator's IEV sign convention (IEV < 0
    -> units issued; IEV > 0 -> in debit).
    """
    vehicle_type = config.classify_vehicle(
        record.adr_category, record.body_on_frame, record.braked_tow_rating_kg
    )
    target = config.emissions_target_g_per_km(vehicle_type, record.performance_year, record.miro_kg)
    delta = record.co2_g_km - target
    net_units = delta * record.units_sold
    return VehicleResult(
        record=record,
        vehicle_type=vehicle_type,
        target_g_per_km=target,
        delta_g_per_km=delta,
        net_units=net_units,
    )


def score_fleet(records: list[VehicleRecord], config: RegulationConfig) -> list[VehicleResult]:
    return [classify_and_score(r, config) for r in records]
