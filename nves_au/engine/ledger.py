"""Credit banking ledger: issuance, 3-year expiry, transfers, penalty exposure.

Sign convention throughout matches the Regulator's IEV convention: a
negative interim emissions value (IEV) is a surplus that issues NVES units
(credits); a positive IEV is a debit. Debits are extinguished against
previously banked credits oldest-vintage-first, so soon-to-expire units are
used up before fresher ones -- this is the economically sensible policy for
an entity that wants to avoid wasting banked credits, and is this project's
own modelling choice (NVES does not mandate a particular consumption order).

Per config/regulation/credits_penalties.yaml (`unverified`): a credit lot
issued in year Y is treated as valid for use in processing years
Y, Y+1, ..., Y + expiry_years - 1, and expires at the start of year
Y + expiry_years if still unused.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from nves_au.config import RegulationConfig
from nves_au.engine.models import SupplierYearPosition


@dataclass
class CreditLot:
    issuance_year: int
    units_remaining: float


@dataclass
class LedgerEntry:
    year: int
    supplier: str
    kind: str  # issuance | extinguishment | expiry | transfer_out | transfer_in
    units: float
    counterparty: str | None = None
    note: str = ""


@dataclass(frozen=True)
class PenaltyExposure:
    """Estimated exposure if `outstanding_debit_units` were never extinguished.

    This models the Regulator's final emissions value (FEV) calculation --
    FEV = IEV - units extinguished -- as if no further units were acquired
    before the FEV is issued. It is an *estimate*, not a determination: the
    real FEV is issued 2 years after the IEV (see
    RegulationConfig.fev_issued_years_after_iev), giving the supplier time to
    acquire or bank more units before the figure crystallises.
    """

    fev_units: float
    infringement_notice_aud: float
    max_civil_penalty_aud: float


@dataclass
class CreditLedger:
    """Multi-supplier credit banking ledger."""

    config: RegulationConfig
    _lots: dict[str, list[CreditLot]] = field(default_factory=lambda: defaultdict(list))
    entries: list[LedgerEntry] = field(default_factory=list)

    def _expire(self, supplier: str, as_of_year: int) -> None:
        expiry_years = self.config.credit_expiry_years()
        still_valid = []
        for lot in self._lots[supplier]:
            if as_of_year >= lot.issuance_year + expiry_years:
                if lot.units_remaining > 1e-9:
                    self.entries.append(
                        LedgerEntry(
                            year=as_of_year,
                            supplier=supplier,
                            kind="expiry",
                            units=lot.units_remaining,
                            note=f"lot issued {lot.issuance_year}",
                        )
                    )
            else:
                still_valid.append(lot)
        self._lots[supplier] = still_valid

    def balance(self, supplier: str, as_of_year: int) -> float:
        """Valid (non-expired) banked credit units for a supplier as of a year."""
        self._expire(supplier, as_of_year)
        return sum(lot.units_remaining for lot in self._lots[supplier])

    def process_period(self, supplier: str, year: int, iev_units: float) -> float:
        """Apply one period's IEV: bank a credit, or extinguish a debit against
        existing banked credits (oldest vintage first).

        Returns the outstanding (unextinguished) debit for this period --
        0.0 if the period was a credit or the debit was fully covered.
        """
        self._expire(supplier, year)

        if iev_units < 0:
            units = -iev_units
            self._lots[supplier].append(CreditLot(issuance_year=year, units_remaining=units))
            self.entries.append(
                LedgerEntry(year=year, supplier=supplier, kind="issuance", units=units)
            )
            return 0.0

        if iev_units > 0:
            remaining_debit = iev_units
            self._lots[supplier].sort(key=lambda lot: lot.issuance_year)
            for lot in self._lots[supplier]:
                if remaining_debit <= 1e-9:
                    break
                if lot.units_remaining <= 1e-9:
                    continue
                used = min(lot.units_remaining, remaining_debit)
                lot.units_remaining -= used
                remaining_debit -= used
                self.entries.append(
                    LedgerEntry(
                        year=year,
                        supplier=supplier,
                        kind="extinguishment",
                        units=used,
                        note=f"from lot issued {lot.issuance_year}",
                    )
                )
            self._lots[supplier] = [
                lot for lot in self._lots[supplier] if lot.units_remaining > 1e-9
            ]
            return max(remaining_debit, 0.0)

        return 0.0

    def transfer(self, from_supplier: str, to_supplier: str, year: int, units: float) -> None:
        """Move `units` of banked credit from one supplier to another, preserving vintage."""
        if units <= 0:
            raise ValueError("transfer units must be positive")
        self._expire(from_supplier, year)
        available = self.balance(from_supplier, year)
        if units > available + 1e-9:
            raise ValueError(
                f"{from_supplier} only has {available:.2f} valid units as of {year}, "
                f"cannot transfer {units:.2f}"
            )
        remaining = units
        self._lots[from_supplier].sort(key=lambda lot: lot.issuance_year)
        for lot in self._lots[from_supplier]:
            if remaining <= 1e-9:
                break
            if lot.units_remaining <= 1e-9:
                continue
            used = min(lot.units_remaining, remaining)
            lot.units_remaining -= used
            remaining -= used
            self._lots[to_supplier].append(
                CreditLot(issuance_year=lot.issuance_year, units_remaining=used)
            )
            self.entries.append(
                LedgerEntry(
                    year=year, supplier=from_supplier, kind="transfer_out",
                    units=used, counterparty=to_supplier,
                )
            )
            self.entries.append(
                LedgerEntry(
                    year=year, supplier=to_supplier, kind="transfer_in",
                    units=used, counterparty=from_supplier,
                )
            )
        self._lots[from_supplier] = [
            lot for lot in self._lots[from_supplier] if lot.units_remaining > 1e-9
        ]

    def penalty_exposure(self, outstanding_debit_units: float) -> PenaltyExposure:
        if outstanding_debit_units <= 0:
            return PenaltyExposure(0.0, 0.0, 0.0)
        rate = self.config.infringement_notice_rate_aud_per_unit()
        max_rate = self.config.max_civil_penalty_rate_aud_per_unit()
        return PenaltyExposure(
            fev_units=outstanding_debit_units,
            infringement_notice_aud=outstanding_debit_units * rate,
            max_civil_penalty_aud=outstanding_debit_units * max_rate,
        )


@dataclass(frozen=True)
class PeriodOutcome:
    supplier: str
    performance_year: int
    iev_units: float
    outstanding_debit_units: float
    bank_balance_after: float
    penalty: PenaltyExposure


def run_ledger(
    positions: list[SupplierYearPosition], config: RegulationConfig
) -> tuple[CreditLedger, list[PeriodOutcome]]:
    """Process a set of supplier/year positions through a fresh ledger, in
    chronological order per supplier (required for expiry/extinguishment to
    be computed correctly).
    """
    ledger = CreditLedger(config=config)
    outcomes = []
    for position in sorted(positions, key=lambda p: (p.supplier, p.performance_year)):
        outstanding = ledger.process_period(
            position.supplier, position.performance_year, position.iev_units
        )
        balance_after = ledger.balance(position.supplier, position.performance_year)
        outcomes.append(
            PeriodOutcome(
                supplier=position.supplier,
                performance_year=position.performance_year,
                iev_units=position.iev_units,
                outstanding_debit_units=outstanding,
                bank_balance_after=balance_after,
                penalty=ledger.penalty_exposure(outstanding),
            )
        )
    return ledger, outcomes
