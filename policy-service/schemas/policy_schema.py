from datetime import date
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel


class PolicyStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    EXPIRED = "EXPIRED"


class CoverageType(str, Enum):
    TIERS = "TIERS"
    TOUS_RISQUES = "TOUS_RISQUES"


class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
        use_enum_values=True,
    )


class PolicyFields(CamelModel):
    client_name: Optional[str] = Field(None, min_length=1, examples=["Jean Dupont"])
    vehicle_model: Optional[str] = Field(None, min_length=1, examples=["Peugeot 208"])
    premium_amount: float = Field(0.0, ge=0, description="Prime annuelle (>= 0)", examples=[550.0])
    client_id: Optional[str] = Field(None, examples=["CLI-001"])
    license_plate: Optional[str] = Field(None, examples=["AB-123-CD"])
    status: PolicyStatus = PolicyStatus.ACTIVE
    coverage_type: Optional[CoverageType] = None
    coverage_limit: float = Field(0.0, ge=0, description="Plafond de remboursement (>= 0)", examples=[25000.0])
    deductible: float = Field(0.0, ge=0, description="Franchise (>= 0)", examples=[300.0])
    start_date: Optional[date] = Field(None, examples=["2026-01-01"])
    end_date: Optional[date] = Field(None, examples=["2026-12-31"])

    @model_validator(mode="after")
    def check_dates(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("endDate doit être postérieure ou égale à startDate.")
        return self


class PolicyCreate(PolicyFields):
    policy_id: str = Field(..., min_length=1, examples=["POL-2026-003"])


class PolicyUpdate(PolicyFields):
    pass


class PolicyResponse(PolicyFields):
    policy_id: str


class PolicyValidityResponse(CamelModel):
    policy_id: str
    check_date: date
    valid: bool
    status: PolicyStatus
    coverage_type: Optional[CoverageType] = None
    coverage_limit: float
    deductible: float
    reasons: List[str] = Field(default_factory=list, description="Raisons de l'invalidité (vide si valide)")
