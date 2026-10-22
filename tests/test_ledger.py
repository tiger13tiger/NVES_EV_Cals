import pytest

from nves_au.engine.ledger import CreditLedger, run_ledger
from nves_au.engine.models import SupplierYearPosition


# -- Worked Example 6: banking, extinguishment, and 3-year expiry --
#
# Supplier X:
#   2025  IEV = -1000  -> issues a 1,000-unit credit lot (vintage 2025, expires
#                          at the start of 2028: valid for use in 2025-2027)
#   2026  IEV = +400   -> extinguished from the 2025 lot; 600 units remain
#   2027  IEV = 0      -> no change; 600 units still banked
#   2028  the 2025 lot has now expired (2028 >= 2025 + 3) -> balance resets to 0
#   2028  IEV = +100   -> no valid credit left to extinguish it -> outstanding
#                          debit of 100 units, penalty exposure applies
def test_banking_extinguishment_and_expiry(config):
    positions = [
        SupplierYearPosition(
            supplier="X", performance_year=2025, total_units_sold=1, iev_units=-1000
        ),
        SupplierYearPosition(
            supplier="X", performance_year=2026, total_units_sold=1, iev_units=400
        ),
        SupplierYearPosition(
            supplier="X", performance_year=2027, total_units_sold=1, iev_units=0
        ),
        SupplierYearPosition(
            supplier="X", performance_year=2028, total_units_sold=1, iev_units=100
        ),
    ]
    ledger, outcomes = run_ledger(positions, config)

    by_year = {o.performance_year: o for o in outcomes}
    assert by_year[2025].outstanding_debit_units == 0
    assert by_year[2025].bank_balance_after == pytest.approx(1000)

    assert by_year[2026].outstanding_debit_units == 0
    assert by_year[2026].bank_balance_after == pytest.approx(600)

    assert by_year[2027].bank_balance_after == pytest.approx(600)

    # the 2025-vintage lot expires before the 2028 debit is processed
    assert by_year[2028].outstanding_debit_units == pytest.approx(100)
    assert by_year[2028].bank_balance_after == pytest.approx(0)

    penalty = by_year[2028].penalty
    assert penalty.fev_units == pytest.approx(100)
    assert penalty.infringement_notice_aud == pytest.approx(100 * 50)
    assert penalty.max_civil_penalty_aud == pytest.approx(100 * 100)

    expiry_entries = [e for e in ledger.entries if e.kind == "expiry"]
    assert any(e.supplier == "X" and e.units == pytest.approx(600) for e in expiry_entries)


def test_no_penalty_when_fully_covered(config):
    positions = [
        SupplierYearPosition(
            supplier="Y", performance_year=2025, total_units_sold=1, iev_units=-500
        ),
        SupplierYearPosition(
            supplier="Y", performance_year=2026, total_units_sold=1, iev_units=500
        ),
    ]
    _, outcomes = run_ledger(positions, config)
    final = outcomes[-1]
    assert final.outstanding_debit_units == 0
    assert final.penalty.infringement_notice_aud == 0
    assert final.penalty.max_civil_penalty_aud == 0


# -- Worked Example 7: transfer between suppliers preserves vintage --
def test_transfer_preserves_vintage_and_expiry(config):
    ledger = CreditLedger(config=config)
    ledger.process_period("A", 2026, -500)  # A banks 500 units, vintage 2026 (expires 2029)

    ledger.transfer("A", "B", 2026, 200)
    assert ledger.balance("A", 2026) == pytest.approx(300)
    assert ledger.balance("B", 2026) == pytest.approx(200)

    # B uses 150 of the transferred units against a 2027 debit
    outstanding = ledger.process_period("B", 2027, 150)
    assert outstanding == 0
    assert ledger.balance("B", 2027) == pytest.approx(50)

    # the transferred lot keeps its original 2026 vintage: expires at the
    # start of 2029, so it's still valid in 2028 but gone by 2029.
    assert ledger.balance("B", 2028) == pytest.approx(50)
    assert ledger.balance("B", 2029) == pytest.approx(0)


def test_transfer_more_than_available_raises(config):
    ledger = CreditLedger(config=config)
    ledger.process_period("A", 2026, -100)
    with pytest.raises(ValueError):
        ledger.transfer("A", "B", 2026, 200)
