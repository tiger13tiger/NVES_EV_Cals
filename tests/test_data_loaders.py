import pytest

from nves_au.data.green_vehicle_guide import GreenVehicleGuideError, load_gvg_export
from nves_au.data.nves_regulator import NvesRegulatorDataError, load_regulator_performance_report


def test_load_gvg_export_with_default_headers(tmp_path):
    csv_path = tmp_path / "gvg.csv"
    csv_path.write_text("Model,CO2 (g/km),Mass (kg)\nZephyr,130,1750\nHauler,230,2300\n")
    df = load_gvg_export(csv_path)
    assert list(df.columns) == ["model_name", "co2_g_km", "mass_kg"]
    assert df.iloc[0]["model_name"] == "Zephyr"
    assert df.iloc[0]["co2_g_km"] == 130


def test_load_gvg_export_missing_column_raises(tmp_path):
    csv_path = tmp_path / "gvg.csv"
    csv_path.write_text("Model,CO2 (g/km)\nZephyr,130\n")
    with pytest.raises(GreenVehicleGuideError):
        load_gvg_export(csv_path)


def test_load_gvg_export_custom_column_map(tmp_path):
    csv_path = tmp_path / "gvg.csv"
    csv_path.write_text("Nom,Emissions,Poids\nZephyr,130,1750\n")
    df = load_gvg_export(
        csv_path,
        column_map={
            "model_name": ["Nom"],
            "co2_g_km": ["Emissions"],
            "mass_kg": ["Poids"],
        },
    )
    assert df.iloc[0]["model_name"] == "Zephyr"


def test_load_regulator_report_with_default_headers(tmp_path):
    csv_path = tmp_path / "regulator.csv"
    csv_path.write_text(
        "Entity,Performance period,IEV,Units issued\n"
        "Acme Motors,2025,-6395,6395\n"
        "Ironclad Trucks,2025,209506,0\n"
    )
    df = load_regulator_performance_report(csv_path)
    assert list(df.columns) == ["supplier", "performance_year", "iev_units", "units_issued"]
    assert df.iloc[0]["supplier"] == "Acme Motors"


def test_load_regulator_report_without_optional_units_issued(tmp_path):
    csv_path = tmp_path / "regulator.csv"
    csv_path.write_text("Entity,Performance period,IEV\nAcme Motors,2025,-6395\n")
    df = load_regulator_performance_report(csv_path)
    assert list(df.columns) == ["supplier", "performance_year", "iev_units"]


def test_load_regulator_report_missing_required_column_raises(tmp_path):
    csv_path = tmp_path / "regulator.csv"
    csv_path.write_text("Entity,IEV\nAcme Motors,-6395\n")
    with pytest.raises(NvesRegulatorDataError):
        load_regulator_performance_report(csv_path)
