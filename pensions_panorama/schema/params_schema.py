"""Pydantic v2 schemas for country pension parameter files (YAML-backed).

Every numeric parameter is wrapped in SourcedValue to ensure each figure
carries a mandatory human-readable citation.  The validator raises on any
missing citation so that the curation discipline is enforced at load-time.
"""

from __future__ import annotations

import logging
import warnings
from enum import Enum
from typing import Any, Union

from pydantic import BaseModel, Field, field_validator, model_validator

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------
class SchemeType(str, Enum):
    BASIC = "basic"         # Universal flat-rate
    TARGETED = "targeted"   # Means-tested / social assistance
    MINIMUM = "minimum"     # Minimum-pension guarantee (top-up)
    DB = "DB"               # Defined-benefit earnings-related
    POINTS = "points"       # Points / notional-unit system
    NDC = "NDC"             # Non-financial (notional) defined contribution
    DC = "DC"               # Financial defined contribution


class SchemeTier(str, Enum):
    FIRST = "first"
    SECOND = "second"
    THIRD = "third"


class IndexationType(str, Enum):
    WAGES = "wages"
    CPI = "CPI"
    MIXED = "mixed"
    FIXED = "fixed"
    NONE = "none"


class CoverageStatus(str, Enum):
    MANDATORY = "mandatory"
    VOLUNTARY = "voluntary"
    EXCLUDED = "excluded"
    UNKNOWN = "unknown"


# ---------------------------------------------------------------------------
# Primitive: every parameter value must carry a source citation
# ---------------------------------------------------------------------------
class SourcedValue(BaseModel):
    """A scalar parameter value with mandatory provenance."""

    value: Union[float, int, str, None] = None
    source_citation: str = Field(
        ...,
        description="Free-text citation (author/year, law reference, publication title).",
    )
    source_url: str | None = None
    year: int | None = Field(None, description="Reference year of this parameter.")
    notes: str | None = None

    @field_validator("source_citation")
    @classmethod
    def citation_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("source_citation must not be empty.")
        return v.strip()


# ---------------------------------------------------------------------------
# Eligibility
# ---------------------------------------------------------------------------
class EligibilityRules(BaseModel):
    normal_retirement_age_male: SourcedValue
    normal_retirement_age_female: SourcedValue
    early_retirement_age_male: SourcedValue | None = None
    early_retirement_age_female: SourcedValue | None = None
    late_retirement_age_male: SourcedValue | None = None
    late_retirement_age_female: SourcedValue | None = None
    vesting_years: SourcedValue | None = None
    minimum_contribution_years: SourcedValue | None = None
    notes: str | None = None


# ---------------------------------------------------------------------------
# Contributions
# ---------------------------------------------------------------------------
class ContributionRules(BaseModel):
    employee_rate: SourcedValue | None = None
    employer_rate: SourcedValue | None = None
    total_rate: SourcedValue | None = None
    contribution_ceiling_aw_multiple: SourcedValue | None = None
    contribution_floor_aw_multiple: SourcedValue | None = None
    contribution_base: str = Field("gross earnings", description="What the rate applies to.")
    notes: str | None = None

    @model_validator(mode="after")
    def at_least_one_rate(self) -> "ContributionRules":
        if (
            self.employee_rate is None
            and self.employer_rate is None
            and self.total_rate is None
        ):
            raise ValueError(
                "ContributionRules must specify at least one of "
                "employee_rate, employer_rate, or total_rate."
            )
        return self


# ---------------------------------------------------------------------------
# Benefit formula rules
# ---------------------------------------------------------------------------
class BenefitRules(BaseModel):
    # --- DB accrual ---
    accrual_rate_per_year: SourcedValue | None = None
    reference_wage: str | None = Field(
        None,
        description="Wage base for DB: 'career_average', 'final_salary', 'best_N_years'.",
    )
    averaging_window_years: SourcedValue | None = None
    valorization: str | None = Field(
        None,
        description="How past wages are revalued: 'wages', 'CPI', 'fixed 0%', etc.",
    )

    # --- Points system ---
    point_value: SourcedValue | None = Field(
        None, description="Monetary value of one pension point (absolute or as %AW)."
    )
    point_cost: SourcedValue | None = Field(
        None, description="Cost of earning one pension point (absolute or as %AW)."
    )

    # --- NDC ---
    notional_interest_rate: str | None = Field(
        None, description="'wages', 'CPI', or a numeric string e.g. '3.5%'."
    )
    annuity_divisor_at_nra: SourcedValue | None = Field(
        None, description="Denominator for converting NDC account to annual pension."
    )

    # --- DC payout ---
    dc_drawdown_type: str | None = Field(
        None, description="'annuity', 'programmed_withdrawal', 'lump_sum'."
    )

    # --- Basic/flat rate ---
    flat_rate_aw_multiple: SourcedValue | None = Field(
        None, description="Benefit as a fraction of average wage (for basic schemes)."
    )
    flat_rate_absolute: SourcedValue | None = Field(
        None, description="Absolute flat-rate benefit amount (currency units)."
    )

    # --- Common constraints ---
    indexation: str | None = Field(
        None, description="Post-retirement indexation: 'wages', 'CPI', 'mixed', 'none'."
    )
    minimum_benefit_aw_multiple: SourcedValue | None = None
    maximum_benefit_aw_multiple: SourcedValue | None = None
    minimum_benefit_absolute: SourcedValue | None = None
    maximum_benefit_absolute: SourcedValue | None = None
    notes: str | None = None


# ---------------------------------------------------------------------------
# Payout / decumulation rules (mainly for DC / NDC)
# ---------------------------------------------------------------------------
class PayoutRules(BaseModel):
    type: str = Field("annuity", description="'annuity', 'programmed_withdrawal', 'lump_sum'.")
    annuity_fee_rate: SourcedValue | None = None
    withdrawal_rate: SourcedValue | None = None
    notes: str | None = None


# ---------------------------------------------------------------------------
# Tax and social-contribution treatment of pensions
# ---------------------------------------------------------------------------
class TaxAndContrib(BaseModel):
    """
    Simplified and extensible tax representation.

    For the initial model, set simplified_net_rate to the effective rate at which
    pension income is subject to tax + employee contributions combined.
    A per-country tax module can override _compute_net() in the tax_engine.
    """

    # Worker-side contributions (applied on wages during accumulation)
    worker_social_contrib_rate: SourcedValue | None = Field(
        None, description="Total employee social security contribution rate on wages."
    )
    worker_income_tax_treatment: str | None = Field(
        None,
        description="'EET', 'TEE', 'TTE', 'ETT', or free-text description.",
    )

    # Pensioner-side
    income_tax_on_pension: str | None = Field(
        None,
        description="Description of income-tax treatment of pension income.",
    )
    pensioner_social_contrib_rate: SourcedValue | None = Field(
        None, description="Social contribution rate on pension income, if any."
    )
    pension_specific_exemption: str | None = None
    pension_tax_allowance_aw_multiple: SourcedValue | None = None

    # Simplified aggregate
    simplified_net_rate: SourcedValue | None = Field(
        None,
        description=(
            "Effective combined tax + employee-contrib rate on pension income. "
            "Used when full tax schedule is unavailable. "
            "E.g. 0.08 means 8 % deducted; net = gross × (1 − rate)."
        ),
    )
    notes: str | None = None


# ---------------------------------------------------------------------------
# Average-earnings data source specification
# ---------------------------------------------------------------------------
class AverageEarnings(BaseModel):
    """
    Specifies where to obtain the average earnings figure used as the numeraire.

    Preferred: pull from ILOSTAT via the stored series ID.
    Fallback: manually entered value with citation.
    """

    ilostat_series_id: str | None = Field(
        None,
        description="ILOSTAT SDMX series identifier, e.g. 'EAR_4MTH_SEX_ECO_CUR_NB'.",
    )
    ilostat_ref_area: str | None = Field(
        None, description="Reference area code as used in the SDMX query."
    )
    ilostat_transformation: str | None = Field(
        None,
        description=(
            "Optional Python expression transforming the raw series value. "
            "Use 'x' as the variable, e.g. 'x * 12' to annualise monthly data."
        ),
    )
    manual_value: float | None = Field(
        None, description="Fallback annual average earnings (in national currency)."
    )
    currency: str | None = None
    year: int | None = None
    source_citation: str = Field(..., description="Citation for the earnings figure.")
    source_url: str | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def must_have_source(self) -> "AverageEarnings":
        if self.ilostat_series_id is None and self.manual_value is None:
            raise ValueError(
                "AverageEarnings must specify either ilostat_series_id or manual_value."
            )
        return self


# ---------------------------------------------------------------------------
# Scheme component
# ---------------------------------------------------------------------------
class SchemeComponent(BaseModel):
    scheme_id: str = Field(..., description="Short machine-readable identifier, e.g. 'SSC_DB'.")
    name: str = Field(..., description="Human-readable scheme name.")
    tier: SchemeTier
    type: SchemeType
    coverage: str = Field(
        ...,
        description="Who is covered: 'private employees', 'civil servants', 'all', etc.",
    )
    eligibility: EligibilityRules
    contributions: ContributionRules | None = None
    benefits: BenefitRules
    payout: PayoutRules | None = None
    active: bool = True
    notes: str | None = None

    @field_validator("scheme_id")
    @classmethod
    def scheme_id_no_spaces(cls, v: str) -> str:
        if " " in v:
            raise ValueError("scheme_id must not contain spaces.")
        return v


# ---------------------------------------------------------------------------
# Worker-type models
# ---------------------------------------------------------------------------

class WorkerTypeEligibilityOverride(BaseModel):
    """Per-worker-type overrides to the scheme-level eligibility rules."""
    normal_retirement_age_male: SourcedValue | None = None
    normal_retirement_age_female: SourcedValue | None = None
    early_retirement_age_male: SourcedValue | None = None
    early_retirement_age_female: SourcedValue | None = None
    vesting_years: SourcedValue | None = None
    minimum_contribution_years: SourcedValue | None = None
    notes: str | None = None


class WorkerTypeContribOverride(BaseModel):
    """Per-worker-type overrides to the scheme-level contribution rules."""
    employee_rate: SourcedValue | None = None
    employer_rate: SourcedValue | None = None
    total_rate: SourcedValue | None = None
    contribution_ceiling_aw_multiple: SourcedValue | None = None
    notes: str | None = None


class SpecialProvisions(BaseModel):
    """Special provisions for a worker type (lump sum, survivor, disability, etc.)."""
    lump_sum: str | None = None
    survivor_benefit: str | None = None
    disability_benefit: str | None = None
    partial_pension: str | None = None
    notes: str | None = None


class WorkerTypeRules(BaseModel):
    """Rules governing how a specific worker category is treated under the pension system."""
    label: str
    coverage_status: CoverageStatus
    scheme_ids: list[str] = []       # must reference valid scheme IDs
    eligibility_override: WorkerTypeEligibilityOverride | None = None
    contributions_override: WorkerTypeContribOverride | None = None
    special_provisions: SpecialProvisions | None = None
    inherit: str | None = None       # worker_type_id to copy from first
    source_citation: str = ""
    source_url: str | None = None
    notes: str | None = None


# ---------------------------------------------------------------------------
# Country metadata
# ---------------------------------------------------------------------------
class CountryMetadata(BaseModel):
    country_name: str
    iso3: str = Field(..., min_length=3, max_length=3)
    iso2: str | None = Field(None, min_length=2, max_length=2)
    currency: str
    currency_code: str = Field(..., description="ISO 4217 currency code, e.g. 'JOD'.")
    reference_year: int
    wb_region: str | None = None
    wb_income_level: str | None = None
    un_location_id: int | None = Field(
        None, description="UN Population Division location ID for life-table queries."
    )
    sources: list[str] = Field(
        default_factory=list,
        description="Primary legislative / institutional references.",
    )
    last_reviewed: str | None = Field(
        None, description="ISO date string of the last human review."
    )


# ---------------------------------------------------------------------------
# Root country parameters
# ---------------------------------------------------------------------------
class CountryParams(BaseModel):
    """Root model for a country YAML parameter file."""

    metadata: CountryMetadata
    schemes: list[SchemeComponent] = Field(..., min_length=1)
    taxes: TaxAndContrib
    average_earnings: AverageEarnings
    worker_types: dict[str, WorkerTypeRules] = Field(default_factory=dict)
    notes: str | None = None

    @field_validator("schemes")
    @classmethod
    def scheme_ids_unique(cls, v: list[SchemeComponent]) -> list[SchemeComponent]:
        ids = [s.scheme_id for s in v]
        if len(ids) != len(set(ids)):
            raise ValueError("scheme_id values must be unique within a country.")
        return v

    @model_validator(mode="after")
    def validate_worker_types(self) -> "CountryParams":
        wt = self.worker_types
        if not wt:
            warnings.warn(
                f"[{self.metadata.iso3}] No worker_types defined. "
                "This field will become mandatory in a future release. "
                "Add at minimum 'private_employee' and 'self_employed' keys.",
                DeprecationWarning,
                stacklevel=2,
            )
            return self

        # 1. self_employed key must exist
        if "self_employed" not in wt:
            raise ValueError(
                "worker_types must include a 'self_employed' key. "
                "Use coverage_status: 'unknown' if data is not yet available."
            )

        # 2. All scheme_ids referenced must exist in self.schemes
        valid_scheme_ids = {s.scheme_id for s in self.schemes}
        for wt_id, rules in wt.items():
            for sid in rules.scheme_ids:
                if sid not in valid_scheme_ids:
                    raise ValueError(
                        f"worker_types['{wt_id}'].scheme_ids references unknown "
                        f"scheme_id '{sid}'. Valid IDs: {sorted(valid_scheme_ids)}"
                    )

        # 3. All inherit references must point to existing worker_type keys
        for wt_id, rules in wt.items():
            if rules.inherit is not None and rules.inherit not in wt:
                raise ValueError(
                    f"worker_types['{wt_id}'].inherit references unknown "
                    f"worker_type '{rules.inherit}'."
                )

        # 4. Check for inheritance cycles (DFS)
        def _has_cycle(start: str, visited: set[str]) -> bool:
            if start in visited:
                return True
            rules = wt.get(start)
            if rules is None or rules.inherit is None:
                return False
            return _has_cycle(rules.inherit, visited | {start})

        for wt_id in wt:
            if _has_cycle(wt_id, set()):
                raise ValueError(
                    f"Circular inheritance detected in worker_types starting from '{wt_id}'."
                )

        return self

    def resolve_worker_type(self, wt_id: str) -> WorkerTypeRules:
        """Return a fully resolved WorkerTypeRules, merging inherited fields.

        Fields on the child take precedence over inherited fields.
        """
        wt = self.worker_types
        if wt_id not in wt:
            raise KeyError(f"worker_type '{wt_id}' not found.")

        # Build resolution order (DFS, deepest ancestor first)
        order: list[str] = []
        seen: set[str] = set()
        current = wt_id
        while current and current not in seen:
            seen.add(current)
            order.insert(0, current)
            parent = wt[current].inherit
            if parent:
                current = parent
            else:
                break

        if not order:
            return wt[wt_id]

        # Start from the root ancestor and overlay child fields
        base = wt[order[0]].model_copy(deep=True)
        for tid in order[1:]:
            child = wt[tid]
            # Override scalar fields if set on child
            for f in ("label", "coverage_status", "source_citation", "source_url", "notes"):
                child_val = getattr(child, f)
                # For string fields, only override if non-empty/non-None
                if child_val is not None and child_val != "":
                    object.__setattr__(base, f, child_val)
            # scheme_ids: if child has any, use child's list
            if child.scheme_ids:
                object.__setattr__(base, "scheme_ids", child.scheme_ids)
            # Override optional nested models if child specifies them
            if child.eligibility_override is not None:
                object.__setattr__(base, "eligibility_override", child.eligibility_override)
            if child.contributions_override is not None:
                object.__setattr__(base, "contributions_override", child.contributions_override)
            if child.special_provisions is not None:
                object.__setattr__(base, "special_provisions", child.special_provisions)

        # Clear the inherit field on resolved object
        object.__setattr__(base, "inherit", None)
        return base


# ---------------------------------------------------------------------------
# Loader helper
# ---------------------------------------------------------------------------
def load_country_params(yaml_path: Any) -> CountryParams:
    """Load and validate a country YAML parameter file."""
    import yaml as _yaml
    from pathlib import Path as _Path

    path = _Path(yaml_path)
    if not path.exists():
        raise FileNotFoundError(f"Country params file not found: {path}")
    with open(path) as fh:
        raw = _yaml.safe_load(fh)
    return CountryParams.model_validate(raw)
