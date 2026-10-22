"""Aggregation of per-vehicle results by supplier, year and type."""

from __future__ import annotations

from collections import defaultdict

from nves_au.engine.models import SupplierTypeYearSummary, SupplierYearPosition, VehicleResult


def aggregate_by_supplier_type_year(
    results: list[VehicleResult],
) -> list[SupplierTypeYearSummary]:
    """Breakdown by (supplier, vehicle_type, performance_year) -- for reporting."""
    groups: dict[tuple[str, str, int], list[VehicleResult]] = defaultdict(list)
    for r in results:
        key = (r.record.supplier, r.vehicle_type, r.record.performance_year)
        groups[key].append(r)

    summaries = []
    for (supplier, vehicle_type, year), group in groups.items():
        summaries.append(
            SupplierTypeYearSummary(
                supplier=supplier,
                vehicle_type=vehicle_type,
                performance_year=year,
                total_units_sold=sum(r.record.units_sold for r in group),
                net_units=sum(r.net_units for r in group),
            )
        )
    return sorted(summaries, key=lambda s: (s.supplier, s.performance_year, s.vehicle_type))


def aggregate_by_supplier_year(results: list[VehicleResult]) -> list[SupplierYearPosition]:
    """Combined Type 1 + Type 2 position per (supplier, performance_year).

    This is the level NVES actually banks and penalises at -- see the note
    on SupplierYearPosition.
    """
    groups: dict[tuple[str, int], list[VehicleResult]] = defaultdict(list)
    for r in results:
        key = (r.record.supplier, r.record.performance_year)
        groups[key].append(r)

    positions = []
    for (supplier, year), group in groups.items():
        positions.append(
            SupplierYearPosition(
                supplier=supplier,
                performance_year=year,
                total_units_sold=sum(r.record.units_sold for r in group),
                iev_units=sum(r.net_units for r in group),
            )
        )
    return sorted(positions, key=lambda p: (p.supplier, p.performance_year))
