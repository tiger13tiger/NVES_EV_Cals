import pytest

from nves_au.engine.models import VehicleRecord
from nves_au.engine.targets import classify_and_score, score_fleet


def _record(**overrides):
    defaults = dict(
        supplier="Acme Motors",
        model_name="Zephyr",
        performance_year=2025,
        adr_category="MA",
        miro_kg=1750,
        co2_g_km=130,
        units_sold=500,
    )
    defaults.update(overrides)
    return VehicleRecord(**defaults)


# -- Worked Example 4: a Type 1 vehicle that beats its target (credit) --
# ET = 141 + 0.0663*(1750-1723) = 142.7901; delta = 130 - 142.7901 = -12.7901
# net_units = -12.7901 * 500 = -6395.05 (a credit contribution)
def test_type1_vehicle_credit(config):
    result = classify_and_score(_record(), config)
    assert result.vehicle_type == "type_1"
    assert result.target_g_per_km == pytest.approx(142.7901, abs=1e-6)
    assert result.delta_g_per_km == pytest.approx(-12.7901, abs=1e-6)
    assert result.net_units == pytest.approx(-6395.05, abs=1e-2)


# -- Worked Example 5: a Type 2 vehicle (ute) that misses its target (debit) --
# ET = 210 + 0.0324*(2300-2155) = 214.698; delta = 230 - 214.698 = 15.302
# net_units = 15.302 * 300 = 4590.6 (a debit contribution)
def test_type2_vehicle_debit(config):
    record = _record(
        model_name="Hauler",
        adr_category="NA",
        miro_kg=2300,
        co2_g_km=230,
        units_sold=300,
    )
    result = classify_and_score(record, config)
    assert result.vehicle_type == "type_2"
    assert result.target_g_per_km == pytest.approx(214.698, abs=1e-6)
    assert result.delta_g_per_km == pytest.approx(15.302, abs=1e-6)
    assert result.net_units == pytest.approx(4590.6, abs=1e-1)


def test_mc_tow_reclassification_changes_target_formula(config):
    heavy_wagon = _record(
        model_name="Trailblazer",
        adr_category="MC",
        body_on_frame=True,
        braked_tow_rating_kg=3500,
        miro_kg=2300,
        co2_g_km=220,
        units_sold=50,
    )
    result = classify_and_score(heavy_wagon, config)
    # Reclassified to Type 2 -> uses the Type 2 headline/MAF/RM, not Type 1's.
    assert result.vehicle_type == "type_2"
    expected_target = 210 + 0.0324 * (2300 - 2155)
    assert result.target_g_per_km == pytest.approx(expected_target, abs=1e-6)


def test_score_fleet_preserves_order(config):
    records = [_record(model_name="A"), _record(model_name="B", co2_g_km=100)]
    results = score_fleet(records, config)
    assert [r.record.model_name for r in results] == ["A", "B"]
