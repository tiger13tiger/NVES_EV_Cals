"""NVES calculation engine.

Vehicle classification and the mass-adjusted target formula live in
nves_au.config.RegulationConfig (they're pure regulatory lookups); this
package applies them to fleet data and handles aggregation and banking.
"""

from nves_au.engine.aggregate import aggregate_by_supplier_type_year, aggregate_by_supplier_year
from nves_au.engine.ledger import CreditLedger, PenaltyExposure, PeriodOutcome, run_ledger
from nves_au.engine.models import (
    SupplierTypeYearSummary,
    SupplierYearPosition,
    VehicleRecord,
    VehicleResult,
)
from nves_au.engine.scenario import (
    ScenarioAdjustment,
    ScenarioComparison,
    apply_scenario,
    load_scenario,
    run_scenario,
)
from nves_au.engine.targets import classify_and_score, score_fleet

__all__ = [
    "VehicleRecord",
    "VehicleResult",
    "SupplierTypeYearSummary",
    "SupplierYearPosition",
    "classify_and_score",
    "score_fleet",
    "aggregate_by_supplier_type_year",
    "aggregate_by_supplier_year",
    "CreditLedger",
    "PenaltyExposure",
    "PeriodOutcome",
    "run_ledger",
    "ScenarioAdjustment",
    "ScenarioComparison",
    "apply_scenario",
    "load_scenario",
    "run_scenario",
]
