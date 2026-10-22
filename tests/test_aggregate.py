import pytest

from nves_au.engine.aggregate import aggregate_by_supplier_type_year, aggregate_by_supplier_year
from nves_au.engine.models import VehicleRecord, VehicleResult

# These tests exercise aggregation logic in isolation from the regulation
# config (which only has confirmed 2025 parameters) by building VehicleResult
# objects directly -- score_fleet()/classify_and_score() against real config
# years are covered in test_targets.py.


def _result(supplier, vehicle_type, year, target, co2, units_sold, model_name="M"):
    record = VehicleRecord(
        supplier=supplier,
        model_name=model_name,
        performance_year=year,
        adr_category="MA" if vehicle_type == "type_1" else "NA",
        miro_kg=1800,
        co2_g_km=co2,
        units_sold=units_sold,
    )
    delta = co2 - target
    return VehicleResult(
        record=record,
        vehicle_type=vehicle_type,
        target_g_per_km=target,
        delta_g_per_km=delta,
        net_units=delta * units_sold,
    )


def _fleet_results():
    return [
        _result(
            "Acme Motors", "type_1", 2025, target=142.7901, co2=130,
            units_sold=500, model_name="Zephyr",
        ),
        _result(
            "Acme Motors", "type_2", 2025, target=214.698, co2=230,
            units_sold=300, model_name="Hauler",
        ),
        _result(
            "Acme Motors", "type_1", 2026, target=120.0, co2=100,
            units_sold=400, model_name="Zephyr",
        ),
    ]


def test_aggregate_by_supplier_type_year():
    summaries = aggregate_by_supplier_type_year(_fleet_results())
    keys = {(s.supplier, s.vehicle_type, s.performance_year) for s in summaries}
    assert keys == {
        ("Acme Motors", "type_1", 2025),
        ("Acme Motors", "type_2", 2025),
        ("Acme Motors", "type_1", 2026),
    }
    type1_2025 = next(
        s for s in summaries if s.vehicle_type == "type_1" and s.performance_year == 2025
    )
    assert type1_2025.total_units_sold == 500
    assert type1_2025.net_units == pytest.approx(-6395.05, abs=1e-1)


def test_aggregate_by_supplier_year_combines_types():
    positions = aggregate_by_supplier_year(_fleet_results())
    pos_2025 = next(p for p in positions if p.performance_year == 2025)
    pos_2026 = next(p for p in positions if p.performance_year == 2026)

    # 2025 combines the Type 1 credit (-6395.05) and Type 2 debit (+4590.6)
    assert pos_2025.total_units_sold == 800
    assert pos_2025.iev_units == pytest.approx(-6395.05 + 4590.6, abs=1e-1)
    assert pos_2026.total_units_sold == 400
