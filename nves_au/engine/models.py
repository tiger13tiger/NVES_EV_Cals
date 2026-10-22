"""Core data models for the NVES calculation engine."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from nves_au.config import VehicleType


class VehicleRecord(BaseModel):
    """One supplier/model/variant line for a single NVES performance period.

    "performance_year" is the calendar year the covered vehicles were
    entered on the Register of Approved Vehicles (the NVES reporting
    period), not a model year. "units_sold" is the vehicle count that line
    represents for that period -- the calculation engine treats every unit
    in the line as identical (same CO2 and MIRO), matching how a supplier's
    monthly sales-by-variant data is normally reported.
    """

    model_config = {"frozen": True}

    supplier: str = Field(min_length=1)
    model_name: str = Field(min_length=1)
    performance_year: int = Field(ge=2025)
    adr_category: str = Field(min_length=1)
    body_on_frame: bool = False
    braked_tow_rating_kg: float = Field(default=0, ge=0)
    miro_kg: float = Field(gt=0)
    co2_g_km: float = Field(ge=0)
    units_sold: int = Field(gt=0)

    @field_validator("adr_category")
    @classmethod
    def _upper(cls, v: str) -> str:
        return v.strip().upper()


class VehicleResult(BaseModel):
    """A VehicleRecord after classification and target calculation."""

    model_config = {"frozen": True}

    record: VehicleRecord
    vehicle_type: VehicleType
    target_g_per_km: float
    delta_g_per_km: float  # actual - target; negative = beats target
    # delta_g_per_km * units_sold; negative = credit (surplus), positive = debit
    net_units: float


class SupplierTypeYearSummary(BaseModel):
    """Aggregated result for one supplier, one vehicle type, one period."""

    model_config = {"frozen": True}

    supplier: str
    vehicle_type: VehicleType
    performance_year: int
    total_units_sold: int
    net_units: float  # sum of net_units across vehicles in this group


class SupplierYearPosition(BaseModel):
    """A supplier's combined (Type 1 + Type 2) position for one period.

    NVES pools Type 1 and Type 2 vehicles into a single interim emissions
    value per regulated entity per period -- the type-level breakdown above
    is for analysis, but credits/debits are banked and extinguished at this
    combined level.
    """

    model_config = {"frozen": True}

    supplier: str
    performance_year: int
    total_units_sold: int
    iev_units: float  # interim emissions value; negative = credit, positive = debit
