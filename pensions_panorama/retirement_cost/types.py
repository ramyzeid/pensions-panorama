"""Dataclasses for retirement cost calculation."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RetirementInputs:
    country_iso3: str
    retirement_age: int
    sex: str                  # 'male' | 'female' | 'total'
    scenario: str             # 'basic' | 'moderate' | 'comfortable'

    # Retirement horizon
    remaining_le_years: Optional[float]
    hale_at_retirement: Optional[float]
    horizon_method: str       # 'UN_WPP_exact' | 'WHO_GHO_LE60_proxy' | 'insufficient'

    # Annual cost components (local currency)
    hfce_pc_lc: Optional[float]          # HFCE per capita in LCU (Tier 3 base)
    che_pc_usd: Optional[float]          # Current health expenditure pc (USD)
    oop_pct_che: Optional[float]         # OOP as % of CHE
    ppp_factor: Optional[float]          # LCU per international $
    gdp_pc_usd: Optional[float]          # GDP per capita USD (wage proxy)
    national_poverty_line_annual_lc: Optional[float] = None  # Tier 1 (if available)

    # Assumptions
    discount_rate: float = 0.04
    inflation_rate: float = 0.03
    age_uplift_factor: float = 1.5
    include_health_oop: bool = True
    use_hale_split: bool = True

    # Source citations [{source, code, year, url, proxy_used}]
    sources: list[dict] = field(default_factory=list)
    data_quality: dict = field(default_factory=dict)


@dataclass
class RetirementResult:
    # Horizon
    retirement_horizon_years: Optional[float]
    healthy_years: Optional[float]
    unhealthy_years: Optional[float]
    horizon_method: str

    # Annual
    annual_consumption_target_lc: Optional[float]
    annual_health_oop_lc: Optional[float]
    annual_total_lc: Optional[float]
    annual_total_ppp_usd: Optional[float]
    consumption_tier: Optional[str]

    # Lifetime
    pv_lifetime_cost_lc: Optional[float]
    undiscounted_lifetime_cost_lc: Optional[float]
    required_monthly_income_lc: Optional[float]

    # Ratios
    ratio_to_gdp_pc: Optional[float]
    ratio_to_poverty_line: Optional[float]

    # Metadata
    data_quality: dict
    sources: list[dict]
