# nves-au

[![CI](https://github.com/tiger13tiger/NVES_EV_Cals/actions/workflows/ci.yml/badge.svg)](https://github.com/tiger13tiger/NVES_EV_Cals/actions/workflows/ci.yml)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

An open-source Python toolkit for Australia's **New Vehicle Efficiency
Standard (NVES)**: calculate a fleet's mass-adjusted CO2 targets,
credit/debit position, banked-credit ledger (with 3-year expiry and
transfers) and estimated penalty exposure -- then run "what if" sales-mix
scenarios. Built for a single analyst at a car supplier to `pip install`
and use without procurement or IT approval. Runs fully local; nothing is
sent to a third party.

**[中文说明 / Chinese README](README.zh-CN.md)**

> ## ⚠️ Not legal or tax advice
>
> This tool is a personal/portfolio open-source project, not a compliance
> product. Several regulatory parameters it uses are **unverified**
> against the primary legislative text (see the table below and
> [`config/regulation/README.md`](config/regulation/README.md)). Always
> confirm every figure against the NVES Act 2024, the NVES Rules, Ministerial
> Determinations and NVES Regulator guidance before relying on it for any
> real compliance, financial or legal decision.

## 60-second quick start

```bash
git clone https://github.com/tiger13tiger/NVES_EV_Cals.git
cd NVES_EV_Cals
pip install -e ".[app]"

nves-au demo                    # run the full pipeline on a synthetic fleet
streamlit run nves_au/app/streamlit_app.py   # interactive dashboard
```

Bring your own data instead of the synthetic fleet:

```bash
nves-au calc examples/sample_fleet.csv
nves-au simulate examples/sample_fleet.csv examples/sample_scenario.yaml
```

Your fleet CSV needs these columns (see `examples/sample_fleet.csv`):

```
supplier, model_name, performance_year, adr_category, body_on_frame,
braked_tow_rating_kg, miro_kg, co2_g_km, units_sold
```

## What it does

1. **Calculation engine** -- classifies each vehicle as Type 1 (passenger)
   or Type 2 (light commercial), computes its mass-adjusted CO2 target,
   and its credit/debit contribution; aggregates by supplier, year and
   type; banks credits with 3-year expiry, extinguishes debits oldest-lot
   first, supports transfers between suppliers, and estimates penalty
   exposure (infringement notice and maximum civil penalty rates).
2. **Scenario simulator** -- apply sales-mix changes (e.g. +1,000 units of
   model A, -500 of model B) and compare the resulting credit position and
   penalty risk against the baseline.
3. **Public data loaders** -- helpers for the Green Vehicle Guide (model
   CO2/mass) and NVES Regulator performance reports, each with a
   documented manual-download step (see `nves_au/data/`).
4. **Synthetic data generator** -- a reproducible, fictional multi-brand
   fleet for demos and tests (no real manufacturer data).
5. **Streamlit app** -- upload a CSV or use the synthetic fleet, view the
   credit position, run scenarios, see a supplier league table. English
   and Simplified Chinese UI.
6. **CLI** -- `nves-au demo`, `nves-au calc <file>`,
   `nves-au simulate <file> <scenario.yaml>`.

Full formulas, citations and hand-calculated worked examples:
**[docs/methodology.md](docs/methodology.md)**.

## Parameter verification status

Every number the engine uses lives in [`config/regulation/`](config/regulation/)
as versioned YAML with its source URL, retrieval date and a confidence
flag -- never hard-coded in the calculation logic. This project's research
pass used web search only (direct fetches to legislation.gov.au and
nvesregulator.gov.au were blocked by network policy in that session), so
treat the table below as a starting point for your own verification, not a
finished audit.

| Parameter | Status | Note |
|---|---|---|
| Headline CO2 targets, 2025-2029 (Type 1 & 2) | ✅ Confirmed | 2 independent sources agree |
| Mass-adjustment formula (`ET = HL + MAF×(DM−RM)`) | ✅ Confirmed | cites NVES Act s.21 |
| Mass-adjustment factor / reference MIRO, **2025** | ✅ Confirmed | Dept. of Infrastructure guidance note |
| Mass-adjustment factor / reference MIRO, **2026+** | ⛔ Not set | left absent on purpose -- Dept. says these may change by Ministerial Determination |
| Mass breakpoints (floor/cap, kg) | ✅ Confirmed | |
| Type 1 / Type 2 classification rule | ⚠️ Unverified | MA/MB/MC vs NA/NB1, MC→Type 2 tow-rating carve-out |
| IEV / FEV accounting | 🟡 Mixed | formula corroborated; "1 unit = 1 g/km×vehicle" is this project's own inference |
| Infringement notice ($50/unit) & max civil penalty ($100/unit) | ✅ Confirmed | 2 independent sources agree |
| Credit banking expiry (3 years) | ⚠️ Unverified | only 1-2 secondary sources |

See [`config/regulation/README.md`](config/regulation/README.md) for what
"confirmed" and "unverified" mean here, and the full source list in
[docs/methodology.md](docs/methodology.md).

## Project layout

```
nves_au/
  config.py        regulation parameter loader (reads config/regulation/*.yaml)
  engine/          classification, targets, aggregation, banking ledger, scenario simulator
  data/            Green Vehicle Guide + NVES Regulator loaders (manual-download based)
  synthetic/       fictional demo fleet generator
  app/             Streamlit dashboard (en/zh)
  cli.py           Typer CLI
config/regulation/ versioned regulatory parameters, with sources
tests/             unit tests incl. hand-calculated worked examples
examples/          sample fleet CSV + scenario YAML
docs/              methodology.md
```

## Development

```bash
pip install -e ".[dev,app]"
ruff check nves_au tests
pytest --cov=nves_au
```

See [CONTRIBUTING.md](CONTRIBUTING.md), especially before touching
`config/regulation/` -- every parameter change needs a source URL,
retrieval date and confidence flag.

## License

Apache License 2.0 -- see [LICENSE](LICENSE). No proprietary DMS schemas,
former-employer data or code were used anywhere in this project.
