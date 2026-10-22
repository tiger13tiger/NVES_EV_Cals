"""Typer CLI for nves-au: `nves-au demo|calc|simulate`."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from nves_au.config import ConfigError, RegulationConfig, load_regulation_config
from nves_au.engine import (
    SupplierYearPosition,
    aggregate_by_supplier_year,
    load_scenario,
    run_ledger,
    run_scenario,
    score_fleet,
)
from nves_au.engine.ledger import PeriodOutcome
from nves_au.io import read_fleet_csv
from nves_au.synthetic import generate_demo_fleet

app = typer.Typer(
    help="nves-au: NVES fleet CO2 target, credit/debit, banking and penalty-exposure calculator.",
    no_args_is_help=True,
)
console = Console()

NOT_LEGAL_ADVICE = (
    "[bold yellow]This is not legal or tax advice.[/bold yellow] Several regulation "
    "parameters used here are unverified against primary legislation -- see below "
    "and config/regulation/README.md. Confirm every figure against the NVES Act, "
    "Rules and Regulator guidance before relying on it for a compliance decision."
)


def _print_unverified_banner(config: RegulationConfig) -> None:
    notes = config.unverified_notes()
    if not notes:
        return
    console.print(NOT_LEGAL_ADVICE)
    table = Table(title="Parameters not fully confirmed against primary sources")
    table.add_column("Config file")
    table.add_column("Confidence")
    for note in notes:
        table.add_row(note.file, note.confidence)
    console.print(table)
    console.print()


def _print_ledger_table(outcomes: list[PeriodOutcome], title: str) -> None:
    table = Table(title=title)
    columns = (
        "Supplier", "Year", "IEV (units)", "Outstanding debit",
        "Bank balance", "Infringement notice (AUD)",
    )
    for col in columns:
        table.add_column(col)
    for o in sorted(outcomes, key=lambda o: (o.supplier, o.performance_year)):
        table.add_row(
            o.supplier,
            str(o.performance_year),
            f"{o.iev_units:,.1f}",
            f"{o.outstanding_debit_units:,.1f}",
            f"{o.bank_balance_after:,.1f}",
            f"{o.penalty.infringement_notice_aud:,.0f}",
        )
    console.print(table)


def _run_and_print(config: RegulationConfig, fleet, title: str) -> list[PeriodOutcome]:
    results = score_fleet(fleet, config)
    positions: list[SupplierYearPosition] = aggregate_by_supplier_year(results)
    _, outcomes = run_ledger(positions, config)
    _print_ledger_table(outcomes, title)
    return outcomes


@app.command()
def demo(
    years: list[int] = typer.Option([2025], help="Performance years to simulate."),
    seed: int = typer.Option(42, help="RNG seed for the synthetic fleet."),
    export_csv: Path | None = typer.Option(
        None, help="Also write the synthetic fleet to this CSV path."
    ),
) -> None:
    """Run the full pipeline against a reproducible synthetic demo fleet."""
    config = load_regulation_config()
    _print_unverified_banner(config)

    fleet = generate_demo_fleet(years=tuple(years), seed=seed)
    supplier_count = len({r.supplier for r in fleet})
    console.print(
        f"[bold]Synthetic demo fleet:[/bold] {len(fleet)} model-lines across "
        f"{supplier_count} fictional suppliers, {len(years)} year(s).\n"
    )

    if export_csv is not None:
        from nves_au.io import write_fleet_csv

        write_fleet_csv(fleet, export_csv)
        console.print(f"Wrote synthetic fleet to {export_csv}\n")

    _run_and_print(config, fleet, title="Demo league table (combined Type 1 + Type 2 position)")


@app.command()
def calc(
    file: Path = typer.Argument(..., exists=True, readable=True, help="Fleet CSV file."),
) -> None:
    """Calculate credit/debit position, banking and penalty exposure for a fleet CSV."""
    config = load_regulation_config()
    _print_unverified_banner(config)

    try:
        fleet = read_fleet_csv(file)
    except (ValueError, OSError) as exc:
        console.print(f"[bold red]Could not read fleet file:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc

    try:
        _run_and_print(config, fleet, title=f"Credit/debit position for {file.name}")
    except ConfigError as exc:
        console.print(f"[bold red]Calculation error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc


@app.command()
def simulate(
    file: Path = typer.Argument(..., exists=True, readable=True, help="Baseline fleet CSV file."),
    scenario_file: Path = typer.Argument(
        ..., exists=True, readable=True, help="Scenario YAML file."
    ),
) -> None:
    """Apply a what-if sales-mix scenario and compare the resulting credit position."""
    config = load_regulation_config()
    _print_unverified_banner(config)

    try:
        baseline = read_fleet_csv(file)
        name, adjustments = load_scenario(scenario_file)
        comparison = run_scenario(baseline, adjustments, config, name=name)
    except (ValueError, OSError, ConfigError) as exc:
        console.print(f"[bold red]Scenario error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(f"[bold]Scenario:[/bold] {comparison.name}\n")
    table = Table(title="Before vs after")
    columns = (
        "Supplier", "Year", "IEV before", "IEV after",
        "Notice before (AUD)", "Notice after (AUD)",
    )
    for col in columns:
        table.add_column(col)
    for (supplier, year), (before, after) in comparison.by_supplier_year().items():
        table.add_row(
            supplier,
            str(year),
            f"{before.iev_units:,.1f}",
            f"{after.iev_units:,.1f}",
            f"{before.penalty.infringement_notice_aud:,.0f}",
            f"{after.penalty.infringement_notice_aud:,.0f}",
        )
    console.print(table)


if __name__ == "__main__":
    app()
