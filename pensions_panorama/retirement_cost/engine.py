"""Pure retirement cost calculation functions."""
from __future__ import annotations

import math
from typing import Optional

from .types import RetirementInputs, RetirementResult

SCENARIO_MULTIPLIERS: dict[str, dict[str, float]] = {
    "tier1": {"basic": 1.20, "moderate": 2.00, "comfortable": 3.00},
    "tier3": {"basic": 0.55, "moderate": 0.75, "comfortable": 1.00},
}


def compute_retirement_horizon(
    inputs: RetirementInputs,
) -> tuple[Optional[float], Optional[float], Optional[float]]:
    """Returns (horizon_years, healthy_years, unhealthy_years)."""
    horizon = inputs.remaining_le_years
    if horizon is None:
        return None, None, None

    if inputs.use_hale_split and inputs.hale_at_retirement is not None:
        healthy = min(inputs.hale_at_retirement, horizon)
        unhealthy = max(0.0, horizon - healthy)
    else:
        healthy = horizon * 0.75
        unhealthy = horizon * 0.25

    return horizon, healthy, unhealthy


def compute_annual_consumption(
    inputs: RetirementInputs,
) -> tuple[Optional[float], Optional[str]]:
    """Returns (annual_lc, tier_label)."""
    if inputs.national_poverty_line_annual_lc is not None:
        mult = SCENARIO_MULTIPLIERS["tier1"].get(inputs.scenario, 2.00)
        return inputs.national_poverty_line_annual_lc * mult, "tier1_national_poverty"
    if inputs.hfce_pc_lc is not None:
        mult = SCENARIO_MULTIPLIERS["tier3"].get(inputs.scenario, 0.75)
        return inputs.hfce_pc_lc * mult, "tier3_hfce"
    return None, None


def compute_health_oop(
    inputs: RetirementInputs,
    healthy_years: Optional[float],
    unhealthy_years: Optional[float],
) -> Optional[float]:
    if not inputs.include_health_oop:
        return None
    if inputs.che_pc_usd is None or inputs.oop_pct_che is None or inputs.ppp_factor is None:
        return None

    baseline_lc = (inputs.oop_pct_che / 100.0) * inputs.che_pc_usd * inputs.ppp_factor

    if inputs.use_hale_split and healthy_years is not None and unhealthy_years is not None:
        total = healthy_years + unhealthy_years
        if total > 0:
            hw = healthy_years / total
            uw = unhealthy_years / total
            return baseline_lc * (hw * 1.0 + uw * inputs.age_uplift_factor)
    return baseline_lc


def compute_pv_lifetime(annual: float, horizon: float, g: float, r: float) -> float:
    """Present value of growing annuity."""
    n = max(1, int(math.ceil(horizon)))
    if abs(r - g) < 1e-9:
        return sum(annual / ((1 + r) ** t) for t in range(1, n + 1))
    return max(0.0, annual * (1 - ((1 + g) / (1 + r)) ** n) / (r - g))


def run_calculation(inputs: RetirementInputs) -> RetirementResult:
    """Orchestrate all sub-functions."""
    horizon, healthy, unhealthy = compute_retirement_horizon(inputs)
    annual_consumption, tier = compute_annual_consumption(inputs)
    annual_oop = compute_health_oop(inputs, healthy, unhealthy) if inputs.include_health_oop else None

    annual_total: Optional[float] = None
    if annual_consumption is not None:
        annual_total = annual_consumption + (annual_oop or 0.0)

    annual_total_ppp: Optional[float] = None
    if annual_total and inputs.ppp_factor and inputs.ppp_factor > 0:
        annual_total_ppp = annual_total / inputs.ppp_factor

    pv: Optional[float] = None
    undiscounted: Optional[float] = None
    monthly: Optional[float] = None
    if annual_total and horizon and horizon > 0:
        pv = compute_pv_lifetime(annual_total, horizon, inputs.inflation_rate, inputs.discount_rate)
        undiscounted = annual_total * horizon
        monthly = annual_total / 12.0

    # Poverty line: use national if available, else $2.15/day international
    poverty_lc: Optional[float] = inputs.national_poverty_line_annual_lc
    if poverty_lc is None and inputs.ppp_factor:
        poverty_lc = 2.15 * 365 * inputs.ppp_factor

    ratio_gdp: Optional[float] = None
    if annual_total and inputs.gdp_pc_usd and inputs.ppp_factor and inputs.ppp_factor > 0:
        gdp_lc = inputs.gdp_pc_usd * inputs.ppp_factor
        ratio_gdp = annual_total / gdp_lc

    ratio_poverty: Optional[float] = None
    if annual_total and poverty_lc and poverty_lc > 0:
        ratio_poverty = annual_total / poverty_lc

    return RetirementResult(
        retirement_horizon_years=horizon,
        healthy_years=healthy,
        unhealthy_years=unhealthy,
        horizon_method=inputs.horizon_method,
        annual_consumption_target_lc=annual_consumption,
        annual_health_oop_lc=annual_oop,
        annual_total_lc=annual_total,
        annual_total_ppp_usd=annual_total_ppp,
        consumption_tier=tier,
        pv_lifetime_cost_lc=pv,
        undiscounted_lifetime_cost_lc=undiscounted,
        required_monthly_income_lc=monthly,
        ratio_to_gdp_pc=ratio_gdp,
        ratio_to_poverty_line=ratio_poverty,
        data_quality=inputs.data_quality,
        sources=inputs.sources,
    )
