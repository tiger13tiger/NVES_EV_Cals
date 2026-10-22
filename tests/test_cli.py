from typer.testing import CliRunner

from nves_au.cli import app
from nves_au.io import write_fleet_csv
from nves_au.synthetic import generate_demo_fleet

runner = CliRunner()


def test_demo_command_runs():
    result = runner.invoke(app, ["demo"])
    assert result.exit_code == 0
    assert "Demo league table" in result.stdout


def test_calc_command_runs(tmp_path):
    csv_path = tmp_path / "fleet.csv"
    write_fleet_csv(generate_demo_fleet(years=(2025,)), csv_path)
    result = runner.invoke(app, ["calc", str(csv_path)])
    assert result.exit_code == 0
    assert "Credit/debit position" in result.stdout


def test_calc_command_missing_file_exits_nonzero():
    result = runner.invoke(app, ["calc", "/no/such/file.csv"])
    assert result.exit_code != 0


def test_simulate_command_runs(tmp_path):
    csv_path = tmp_path / "fleet.csv"
    write_fleet_csv(generate_demo_fleet(years=(2025,)), csv_path)
    scenario_path = tmp_path / "scenario.yaml"
    scenario_path.write_text(
        """
name: test scenario
adjustments:
  - supplier: Ironclad Trucks
    model_name: Ironclad Ridge 4x4
    performance_year: 2025
    delta_units: -500
  - supplier: Dragonfly Motors
    model_name: Dragonfly Comet
    performance_year: 2025
    delta_units: 500
"""
    )
    result = runner.invoke(app, ["simulate", str(csv_path), str(scenario_path)])
    assert result.exit_code == 0
    assert "Before vs after" in result.stdout
