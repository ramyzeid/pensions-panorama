"""Pension calculator – personalised benefit computation for a specific person.

This module defines the dataclasses and the top-level ``compute_benefit()``
function that is used by the ``pp calc`` CLI command and the Streamlit
Calculator tab.

The function delegates to the existing PensionEngine internals (_dispatch,
_aggregate, _apply_tax) so the calculation logic is never duplicated.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class PersonProfile:
    """Describes the individual for whom a pension is being calculated."""

    sex: str                          # "male" | "female"
    age: float                        # current age (years)
    service_years: float              # total years of service / contributions
    wage: float                       # annual wage (in wage_unit)
    wage_unit: str = "currency"       # "currency" | "aw_multiple"
    worker_type_id: str = "private_employee"
    contribution_years: float | None = None   # if different from service_years
    dc_account_balance: float | None = None   # optional override for DC schemes
    extra: dict = field(default_factory=dict)  # scheme-specific fields


@dataclass
class EligibilityResult:
    """Eligibility assessment outcome."""

    is_eligible: bool
    missing: list[str]               # human-readable list of what's missing
    normal_retirement_age: float
    early_retirement_age: float | None
    vesting_years: float | None
    years_to_nra: float              # negative means already past NRA


@dataclass
class ReasoningStep:
    """One step in the calculation reasoning trace."""

    label: str
    formula: str
    value: str                       # formatted value
    citation: str | None = None


@dataclass
class BenefitResult:
    """Complete benefit calculation result for one person."""

    worker_type_id: str
    person: PersonProfile
    eligibility: EligibilityResult
    gross_benefit: float
    net_benefit: float
    gross_replacement_rate: float
    net_replacement_rate: float
    gross_pension_level: float
    net_pension_level: float
    component_breakdown: dict[str, float]
    reasoning_trace: list[ReasoningStep]
    warnings: list[str] = field(default_factory=list)
