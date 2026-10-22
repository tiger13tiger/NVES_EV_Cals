"""Loads the versioned NVES regulation parameters from config/regulation/*.yaml.

Nothing in nves_au.engine hard-codes a target, slope, reference mass, penalty
rate or expiry period: every formula goes through RegulationConfig so the
numbers stay auditable against config/regulation/README.md and its cited
sources. A year/type combination that isn't in the YAML raises ConfigError
rather than silently falling back to a neighbouring year's value.
"""

from __future__ import annotations

import importlib.resources
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import yaml

VehicleType = Literal["type_1", "type_2"]

_FILES = (
    "headline_targets.yaml",
    "mass_adjustment.yaml",
    "vehicle_classification.yaml",
    "credits_penalties.yaml",
)


class ConfigError(Exception):
    """Raised when a regulation parameter is missing, not when it's merely unverified."""


def _find_config_dir() -> Path:
    """Locate config/regulation/, preferring the repo checkout over packaged data.

    Editable installs (``pip install -e .``) and running from a source
    checkout both have ``config/regulation`` as a sibling of the ``nves_au``
    package directory. A built wheel instead ships the same files inside the
    package (see the force-include in pyproject.toml), so that's the fallback.
    """
    repo_root_candidate = Path(__file__).resolve().parent.parent / "config" / "regulation"
    if repo_root_candidate.is_dir():
        return repo_root_candidate

    try:
        packaged = importlib.resources.files("nves_au._config_data") / "regulation"
        if packaged.is_dir():
            return Path(str(packaged))
    except (ModuleNotFoundError, FileNotFoundError):
        pass

    raise ConfigError(
        "Could not locate config/regulation/ (checked the repo-root layout and the "
        "packaged nves_au._config_data.regulation fallback). Re-install the package "
        "or run from a full source checkout."
    )


@dataclass(frozen=True)
class SourceNote:
    file: str
    confidence: str
    caveats: str


@dataclass(frozen=True)
class RegulationConfig:
    """In-memory view of every file in config/regulation/."""

    headline_targets: dict
    mass_adjustment: dict
    vehicle_classification: dict
    credits_penalties: dict
    source_notes: list[SourceNote] = field(default_factory=list)

    # -- headline + mass-adjusted target -----------------------------------

    def headline_target_g_per_km(self, vehicle_type: VehicleType, year: int) -> float:
        table = self.headline_targets["headline_targets_g_per_km"][vehicle_type]
        if year not in table:
            raise ConfigError(
                f"No headline target configured for {vehicle_type}, {year}. "
                f"Known years: {sorted(table)}. Add it to "
                "config/regulation/headline_targets.yaml with a source before using it."
            )
        return float(table[year])

    def mass_adjustment_factor(self, vehicle_type: VehicleType, year: int) -> float:
        table = self.mass_adjustment["mass_adjustment_factor"][vehicle_type]
        if year not in table:
            raise ConfigError(
                f"No mass adjustment factor configured for {vehicle_type}, {year}. "
                f"Known years: {sorted(table)}. The Department's guidance note says "
                "2026+ values may change by Ministerial Determination -- confirm and "
                "add them to config/regulation/mass_adjustment.yaml before using them."
            )
        return float(table[year])

    def reference_miro_kg(self, vehicle_type: VehicleType, year: int) -> float:
        table = self.mass_adjustment["reference_miro_kg"][vehicle_type]
        if year not in table:
            raise ConfigError(
                f"No reference MIRO configured for {vehicle_type}, {year}. "
                f"Known years: {sorted(table)}."
            )
        return float(table[year])

    def mass_breakpoints_kg(self, vehicle_type: VehicleType) -> tuple[float, float]:
        entry = self.mass_adjustment["mass_breakpoints_kg"][vehicle_type]
        return float(entry["floor_kg"]), float(entry["cap_kg"])

    def emissions_target_g_per_km(
        self, vehicle_type: VehicleType, year: int, miro_kg: float
    ) -> float:
        """ET = HL + MAF * (DM - RM), DM = miro clamped to the type's breakpoints."""
        headline = self.headline_target_g_per_km(vehicle_type, year)
        maf = self.mass_adjustment_factor(vehicle_type, year)
        reference_miro = self.reference_miro_kg(vehicle_type, year)
        floor_kg, cap_kg = self.mass_breakpoints_kg(vehicle_type)
        designated_mass = min(max(miro_kg, floor_kg), cap_kg)
        return headline + maf * (designated_mass - reference_miro)

    # -- classification -------------------------------------------------

    def classify_vehicle(
        self,
        adr_category: str,
        body_on_frame: bool = False,
        braked_tow_rating_kg: float = 0,
    ) -> VehicleType:
        rule = self.vehicle_classification["type_2_reclassification_rule"]
        type_1_cats = set(self.vehicle_classification["type_1_adr_categories"])
        type_2_cats = set(self.vehicle_classification["type_2_adr_categories"])

        if adr_category == rule["applies_to_adr_category"] and (
            (not rule["requires_body_on_frame"] or body_on_frame)
            and braked_tow_rating_kg >= rule["min_braked_tow_rating_kg"]
        ):
            return "type_2"
        if adr_category in type_1_cats:
            return "type_1"
        if adr_category in type_2_cats:
            return "type_2"
        raise ConfigError(
            f"ADR category '{adr_category}' is not in type_1 ({sorted(type_1_cats)}) or "
            f"type_2 ({sorted(type_2_cats)}) per config/regulation/vehicle_classification.yaml."
        )

    def max_gvm_kg(self) -> float:
        return float(self.vehicle_classification["scope"]["max_gvm_kg"])

    # -- credits, banking, penalties -------------------------------------

    def unit_equals_gram_km_per_vehicle(self) -> bool:
        return bool(self.credits_penalties["accounting"]["unit_equals_gram_km_per_vehicle"])

    def fev_issued_years_after_iev(self) -> int:
        return int(self.credits_penalties["accounting"]["fev_issued_years_after_iev"])

    def credit_expiry_years(self) -> int:
        return int(self.credits_penalties["credit_banking"]["expiry_years_from_issuance"])

    def infringement_notice_rate_aud_per_unit(self) -> float:
        return float(self.credits_penalties["penalties"]["infringement_notice_rate_aud_per_unit"])

    def max_civil_penalty_rate_aud_per_unit(self) -> float:
        return float(self.credits_penalties["penalties"]["max_civil_penalty_rate_aud_per_unit"])

    def infringement_notice_payment_window_days(self) -> int:
        return int(self.credits_penalties["penalties"]["infringement_notice_payment_window_days"])

    # -- transparency -----------------------------------------------------

    def unverified_notes(self) -> list[SourceNote]:
        """Source notes for files/sections whose confidence isn't 'confirmed'."""
        return [n for n in self.source_notes if n.confidence != "confirmed"]


def load_regulation_config(config_dir: Path | None = None) -> RegulationConfig:
    config_dir = config_dir or _find_config_dir()

    data = {}
    notes: list[SourceNote] = []
    for filename in _FILES:
        path = config_dir / filename
        if not path.is_file():
            raise ConfigError(f"Missing required config file: {path}")
        with path.open(encoding="utf-8") as fh:
            parsed = yaml.safe_load(fh)
        data[filename] = parsed
        meta = parsed.get("meta", {})
        notes.append(
            SourceNote(
                file=filename,
                confidence=str(meta.get("confidence", "unknown")),
                caveats=str(meta.get("caveats", "")),
            )
        )

    return RegulationConfig(
        headline_targets=data["headline_targets.yaml"],
        mass_adjustment=data["mass_adjustment.yaml"],
        vehicle_classification=data["vehicle_classification.yaml"],
        credits_penalties=data["credits_penalties.yaml"],
        source_notes=notes,
    )
