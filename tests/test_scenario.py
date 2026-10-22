import pytest

from nves_au.engine.models import VehicleRecord
from nves_au.engine.scenario import ScenarioAdjustment, apply_scenario, run_scenario


def _baseline():
    return [
        VehicleRecord(
            supplier="Acme Motors", model_name="Zephyr", performance_year=2025,
            adr_category="MA", miro_kg=1750, co2_g_km=130, units_sold=1000,
        ),
        VehicleRecord(
            supplier="Acme Motors", model_name="Hauler", performance_year=2025,
            adr_category="NA", miro_kg=2300, co2_g_km=230, units_sold=500,
        ),
    ]


def test_apply_scenario_adjusts_existing_line():
    baseline = _baseline()
    adjustments = [
        ScenarioAdjustment(
            supplier="Acme Motors", model_name="Zephyr", performance_year=2025, delta_units=200
        ),
        ScenarioAdjustment(
            supplier="Acme Motors", model_name="Hauler", performance_year=2025, delta_units=-100
        ),
    ]
    result = apply_scenario(baseline, adjustments)
    zephyr = next(r for r in result if r.model_name == "Zephyr")
    hauler = next(r for r in result if r.model_name == "Hauler")
    assert zephyr.units_sold == 1200
    assert hauler.units_sold == 400
    # baseline list itself must be untouched
    assert baseline[0].units_sold == 1000


def test_apply_scenario_removes_line_at_zero():
    baseline = _baseline()
    adjustments = [
        ScenarioAdjustment(
            supplier="Acme Motors", model_name="Hauler", performance_year=2025, delta_units=-500
        )
    ]
    result = apply_scenario(baseline, adjustments)
    assert all(r.model_name != "Hauler" for r in result)
    assert len(result) == 1


def test_apply_scenario_negative_below_zero_raises():
    baseline = _baseline()
    adjustments = [
        ScenarioAdjustment(
            supplier="Acme Motors", model_name="Hauler", performance_year=2025, delta_units=-600
        )
    ]
    with pytest.raises(ValueError):
        apply_scenario(baseline, adjustments)


def test_apply_scenario_adds_new_model():
    baseline = _baseline()
    adjustments = [
        ScenarioAdjustment(
            supplier="Acme Motors", model_name="Spark EV", performance_year=2025,
            delta_units=300, adr_category="MA", miro_kg=1600, co2_g_km=0,
        )
    ]
    result = apply_scenario(baseline, adjustments)
    spark = next(r for r in result if r.model_name == "Spark EV")
    assert spark.units_sold == 300
    assert spark.co2_g_km == 0


def test_apply_scenario_new_model_missing_fields_raises():
    baseline = _baseline()
    adjustments = [
        ScenarioAdjustment(
            supplier="Acme Motors", model_name="Spark EV", performance_year=2025, delta_units=300
        )
    ]
    with pytest.raises(ValueError):
        apply_scenario(baseline, adjustments)


# -- Worked Example 8: shifting volume toward the cleaner model reduces IEV --
def test_run_scenario_shifts_credit_position(config):
    baseline = _baseline()
    adjustments = [
        ScenarioAdjustment(
            supplier="Acme Motors", model_name="Zephyr", performance_year=2025, delta_units=1000
        ),
        ScenarioAdjustment(
            supplier="Acme Motors", model_name="Hauler", performance_year=2025, delta_units=-500
        ),
    ]
    comparison = run_scenario(baseline, adjustments, config, name="shift-to-zephyr")
    paired = comparison.by_supplier_year()
    baseline_outcome, scenario_outcome = paired[("Acme Motors", 2025)]

    # Removing all Hauler (debit) volume and doubling Zephyr (credit) volume
    # must move the combined IEV further into credit.
    assert scenario_outcome.iev_units < baseline_outcome.iev_units
    assert (
        scenario_outcome.penalty.infringement_notice_aud
        <= baseline_outcome.penalty.infringement_notice_aud
    )
