import pytest

from nves_au.config import ConfigError


def test_headline_targets_2025(config):
    assert config.headline_target_g_per_km("type_1", 2025) == 141
    assert config.headline_target_g_per_km("type_2", 2025) == 210


def test_headline_target_missing_year_raises(config):
    with pytest.raises(ConfigError):
        config.headline_target_g_per_km("type_1", 2099)


def test_mass_adjustment_2026_not_guessed(config):
    """2026+ MAF/RM are explicitly left unset (subject to Ministerial
    Determination per the Department's own guidance note) -- the engine
    must refuse to silently reuse the 2025 values."""
    with pytest.raises(ConfigError):
        config.mass_adjustment_factor("type_1", 2026)
    with pytest.raises(ConfigError):
        config.reference_miro_kg("type_2", 2026)


def test_mass_breakpoints(config):
    floor_1, cap_1 = config.mass_breakpoints_kg("type_1")
    floor_2, cap_2 = config.mass_breakpoints_kg("type_2")
    assert (floor_1, cap_1) == (1500, 2200)
    assert (floor_2, cap_2) == (1500, 2400)


# -- Worked Example 1: Type 1 emissions target, MIRO within the clamp band --
# ET = HL + MAF * (DM - RM) = 141 + 0.0663 * (1750 - 1723) = 142.7901
# This matches the Department of Infrastructure guidance note's own worked
# example input (a Type 1 vehicle with 1,750 kg MIRO in 2025).
def test_emissions_target_worked_example_within_band(config):
    et = config.emissions_target_g_per_km("type_1", 2025, miro_kg=1750)
    assert et == pytest.approx(142.7901, abs=1e-6)


# -- Worked Example 2: designated mass clamped at the upper cap --
# A Type 1 vehicle heavier than the 2,200 kg cap is evaluated AS IF it were
# exactly 2,200 kg: ET = 141 + 0.0663 * (2200 - 1723) = 172.6251
def test_emissions_target_clamped_at_cap(config):
    et_at_cap = config.emissions_target_g_per_km("type_1", 2025, miro_kg=2200)
    et_above_cap = config.emissions_target_g_per_km("type_1", 2025, miro_kg=2500)
    assert et_at_cap == pytest.approx(172.6251, abs=1e-6)
    assert et_above_cap == et_at_cap


# -- Worked Example 3: designated mass clamped at the lower floor --
# A Type 2 vehicle lighter than the 1,500 kg floor is evaluated as if it
# were exactly 1,500 kg: ET = 210 + 0.0324 * (1500 - 2155) = 188.778
def test_emissions_target_clamped_at_floor(config):
    et_at_floor = config.emissions_target_g_per_km("type_2", 2025, miro_kg=1500)
    et_below_floor = config.emissions_target_g_per_km("type_2", 2025, miro_kg=1200)
    assert et_at_floor == pytest.approx(188.778, abs=1e-6)
    assert et_below_floor == et_at_floor


def test_classify_vehicle_passenger_and_commercial(config):
    assert config.classify_vehicle("MA") == "type_1"
    assert config.classify_vehicle("MB") == "type_1"
    assert config.classify_vehicle("NA") == "type_2"
    assert config.classify_vehicle("NB1") == "type_2"


def test_classify_vehicle_mc_default_is_passenger(config):
    # A light off-road passenger wagon (MC) without the heavy-tow carve-out
    # stays Type 1.
    assert config.classify_vehicle("MC", body_on_frame=True, braked_tow_rating_kg=2500) == "type_1"
    assert config.classify_vehicle("MC") == "type_1"


def test_classify_vehicle_mc_heavy_tow_reclassified_type_2(config):
    # Body-on-frame MC wagon with >= 3,000 kg braked tow rating is reclassified.
    assert config.classify_vehicle("MC", body_on_frame=True, braked_tow_rating_kg=3000) == "type_2"
    assert config.classify_vehicle("MC", body_on_frame=True, braked_tow_rating_kg=3500) == "type_2"


def test_classify_vehicle_mc_heavy_tow_without_body_on_frame_stays_type_1(config):
    assert config.classify_vehicle("MC", body_on_frame=False, braked_tow_rating_kg=3500) == "type_1"


def test_classify_vehicle_unknown_category_raises(config):
    with pytest.raises(ConfigError):
        config.classify_vehicle("ZZ")


def test_unverified_notes_present(config):
    # This project's own transparency requirement: anything not sourced
    # directly from primary legislation must self-report as unverified.
    flagged_files = {n.file for n in config.unverified_notes()}
    assert "vehicle_classification.yaml" in flagged_files
    assert "mass_adjustment.yaml" in flagged_files
