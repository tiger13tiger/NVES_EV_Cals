# Methodology

This page explains every formula `nves_au` uses, with citations to the
config file that holds the underlying number and at least three fully
worked, hand-calculated examples. It is a description of how the code
works, not legal advice -- see the disclaimer in the main [README](../README.md).

All regulatory parameters live in [`config/regulation/`](../config/regulation/)
as versioned YAML with a source URL, retrieval date and a confidence flag
(`confirmed` or `unverified`/`mixed`) per file. Nothing below is hard-coded
in `nves_au/engine/` -- every number here is read from those files through
`nves_au.config.RegulationConfig`. **Read
[`config/regulation/README.md`](../config/regulation/README.md) first**: this
project's research pass could not fetch legislation.gov.au or
nvesregulator.gov.au directly (network-blocked), so most figures here are
reconstructed from search-tool summaries of official pages plus
corroborating professional commentary, not read from the primary
legislative text. Several are explicitly flagged `unverified` below.

## 1. Vehicle classification (Type 1 / Type 2)

Source: `config/regulation/vehicle_classification.yaml` (**unverified**).

- **Type 1** (passenger): ADR categories MA, MB, MC.
- **Type 2** (light commercial): ADR categories NA, NB1.
- **Reclassification**: an MC vehicle (e.g. a heavy-duty 4x4 wagon) is
  reclassified from Type 1 to Type 2 if it is body-on-frame construction
  **and** has a braked towing capacity &ge; 3,000 kg.
- NVES covers vehicles up to 4.5 tonnes Gross Vehicle Mass (GVM); low-volume
  and specialist/enthusiast exemptions exist but are out of scope for v1 --
  every input row is assumed to be a regulated, non-exempt covered vehicle.

Implemented in `RegulationConfig.classify_vehicle()` (`nves_au/config.py`).

## 2. Mass-adjusted emissions target

Source: `config/regulation/mass_adjustment.yaml` (2025 confirmed; 2026+
intentionally absent) and `headline_targets.yaml` (confirmed).

```
ET = HL + MAF * (DM - RM)
```

- **ET** -- the vehicle's emissions target (g/km CO2)
- **HL** -- headline target for the vehicle's Type and year
- **MAF** -- mass adjustment factor for the vehicle's Type and year
- **DM** -- "designated mass": the vehicle's Mass In Running Order (MIRO,
  kg), clamped to `[floor_kg, cap_kg]` for its Type
- **RM** -- reference MIRO for the vehicle's Type and year

2025 values: Type 1 HL=141 g/km, MAF=0.0663, RM=1,723 kg, mass band
[1,500, 2,200] kg. Type 2 HL=210 g/km, MAF=0.0324, RM=2,155 kg, mass band
[1,500, 2,400] kg. **2026-2029 mass-adjustment factors and reference MIRO
are not yet set** -- the Department's own guidance note says they may
change by a future Ministerial Determination, so the engine raises a clear
error rather than silently reusing the 2025 values (headline targets for
2026-2029 ARE set; only the mass-adjustment side is pending).

Implemented in `RegulationConfig.emissions_target_g_per_km()`.

### Worked Example 1 -- within the mass band

A Type 1 vehicle, 2025, MIRO 1,750 kg (between the 1,500/2,200 kg band, so
no clamping):

```
ET = 141 + 0.0663 * (1,750 - 1,723) = 141 + 0.0663*27 = 141 + 1.7901 = 142.7901 g/km
```

### Worked Example 2 -- clamped at the upper cap

A Type 1 vehicle, 2025, MIRO 2,500 kg (above the 2,200 kg cap, so DM is
clamped to 2,200 kg):

```
DM = min(max(2500, 1500), 2200) = 2200
ET = 141 + 0.0663 * (2200 - 1723) = 141 + 0.0663*477 = 141 + 31.6251 = 172.6251 g/km
```

A heavier vehicle is evaluated *as if* it were exactly 2,200 kg -- it gets
no further target relief for extra mass beyond the cap.

### Worked Example 3 -- clamped at the lower floor

A Type 2 vehicle, 2025, MIRO 1,200 kg (below the 1,500 kg floor, so DM is
clamped to 1,500 kg):

```
DM = min(max(1200, 1500), 2400) = 1500
ET = 210 + 0.0324 * (1500 - 2155) = 210 + 0.0324*(-655) = 210 - 21.222 = 188.778 g/km
```

A lighter vehicle gets no further target benefit below the floor either.

(All three are asserted exactly in `tests/test_config.py`.)

## 3. Per-vehicle credit/debit

```
delta_i = actual_co2_i - ET_i
net_units_i = delta_i * units_sold_i
```

`net_units_i < 0` is a credit contribution (beats its target);
`> 0` is a debit contribution. Implemented in
`nves_au/engine/targets.py::classify_and_score()`.

### Worked Example 4 -- a credit line

Type 1 vehicle, target 142.7901 g/km (Example 1 above), actual 130 g/km,
500 units sold:

```
delta = 130 - 142.7901 = -12.7901 g/km
net_units = -12.7901 * 500 = -6,395.05  (a credit)
```

### Worked Example 5 -- a debit line

Type 2 vehicle (ute), target = 210 + 0.0324*(2300-2155) = 214.698 g/km,
actual 230 g/km, 300 units sold:

```
delta = 230 - 214.698 = 15.302 g/km
net_units = 15.302 * 300 = 4,590.6  (a debit)
```

## 4. Aggregation

`nves_au/engine/aggregate.py` sums `net_units` by `(supplier, vehicle_type,
performance_year)` for reporting, and separately by `(supplier,
performance_year)` combining both types -- NVES pools Type 1 and Type 2
vehicles into a single **interim emissions value (IEV)** per regulated
entity per period:

```
IEV = sum(net_units_i) over all covered vehicles for that supplier and year
```

`IEV < 0` issues NVES units (credits); `IEV > 0` is a debit. Source:
`config/regulation/credits_penalties.yaml` (**mixed** confidence --
the IEV formula itself is corroborated by the Regulator's own page and a
third-party calculator; see that file's `caveats`).

## 5. Credit banking, expiry and transfers

Source: `config/regulation/credits_penalties.yaml` (**unverified**: the
3-year expiry period and the "1 unit = 1 gram/km x 1 vehicle" equivalence
are each backed by only one or two secondary sources).

- A credit (negative IEV) issues a lot of NVES units dated to its issuance
  year. The lot is valid for use in processing years
  `issuance_year .. issuance_year + 2` and expires at the start of
  `issuance_year + 3` if unused (`credit_expiry_years` in config).
- A debit (positive IEV) is extinguished against existing banked lots,
  **oldest vintage first** (so soon-to-expire units are used before
  fresher ones) -- this consumption order is this project's own modelling
  choice, not something NVES mandates.
- A **final emissions value (FEV)** is issued 2 years after the IEV for the
  same period: `FEV = IEV - units extinguished`. This project estimates
  penalty exposure as if the FEV were determined today from whatever is
  still outstanding, i.e. it is a running estimate, not the actual future
  FEV (which depends on what's extinguished before then).
- Units can be **transferred** between suppliers; a transfer preserves the
  original vintage (and therefore the original expiry date) of the units
  moved.

Implemented in `nves_au/engine/ledger.py::CreditLedger` /
`run_ledger()`.

### Worked Example 6 -- banking, extinguishment and expiry

Supplier X:

| Year | IEV   | What happens                                              | Bank balance after |
|------|-------|------------------------------------------------------------|---------------------|
| 2025 | -1,000| issues a 1,000-unit lot, vintage 2025 (expires start 2028) | 1,000 |
| 2026 | +400  | extinguished from the 2025 lot                              | 600 |
| 2027 | 0     | no change                                                   | 600 |
| 2028 | +100  | the 2025 lot has just expired (2028 >= 2025+3); nothing left to extinguish with | 0 |

In 2028 the supplier has an outstanding debit of 100 units with no banked
credit to cover it -- see Worked Example 7 for the resulting penalty
exposure. (Asserted in `tests/test_ledger.py::test_banking_extinguishment_and_expiry`.)

## 6. Penalties

Source: `config/regulation/credits_penalties.yaml` (**confirmed**: two
independent sources agree).

- **Infringement notice**: `outstanding_units * $50 AUD`, with 28 days to
  pay.
- **Maximum civil penalty** (if a matter proceeds beyond a notice):
  `outstanding_units * $100 AUD`.

Implemented in `nves_au/engine/ledger.py::CreditLedger.penalty_exposure()`.

### Worked Example 7 -- penalty exposure

Continuing Worked Example 6: Supplier X's 2028 outstanding debit is 100
units.

```
infringement_notice = 100 * $50  = $5,000 AUD
max_civil_penalty    = 100 * $100 = $10,000 AUD
```

## 7. Scenario simulator

`nves_au/engine/scenario.py` applies a list of sales-mix adjustments
(change in `units_sold` for an existing model line, or a brand-new model
line) to a baseline fleet, re-runs the whole pipeline above on both the
original and adjusted fleet, and compares the resulting IEV and penalty
exposure per supplier/year. See `examples/sample_scenario.yaml` for the
file format, and `nves-au simulate <fleet.csv> <scenario.yaml>`.

### Worked Example 8 -- shifting volume toward a cleaner model

Baseline: 1,000 units of a Type 1 vehicle at target 142.7901 g/km / actual
130 g/km (credit -6,395.05 units), plus 500 units of a Type 2 ute at target
214.698 g/km / actual 230 g/km (debit +4,590.6 units). Combined baseline
IEV = -1,804.45 (net credit).

Scenario: +1,000 units of the Type 1 vehicle, -500 units of the Type 2 ute
(i.e. all ute volume removed, passenger volume doubled):

```
new Type 1 contribution = -12.7901 * 2000 = -25,580.2
new Type 2 contribution = 0 (line removed)
new combined IEV = -25,580.2  (further into credit than -1,804.45)
```

Confirmed in `tests/test_scenario.py::test_run_scenario_shifts_credit_position`.

## Full source list

See [`config/regulation/README.md`](../config/regulation/README.md) and the
`meta.sources` block at the top of each YAML file for the exact URLs
consulted and what each one contributed. In summary:

- New Vehicle Efficiency Standard Act 2024 (Cth) -- legislation.gov.au, C2024A00034 (not read directly; cited by the Department's guidance note)
- Department of Infrastructure, "NVES numerical precision and calculations guidance note"
- NVES Regulator (nvesregulator.gov.au): obligations, IEV/FEV calculation, infringement notices and penalties, unit registry pages
- ICCT policy brief (June 2024); DieselNet Australia light-duty GHG standards page
- BDO, Bartier, Pitcher, Moulis Legal, Loopit (professional/legal commentary, used only to corroborate, never as a sole source for a `confirmed` figure)
