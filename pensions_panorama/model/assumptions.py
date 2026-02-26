"""Global modeling assumptions loader and dataclass.

Assumptions are stored in data/params/assumptions.yaml and loaded once
per run.  The dataclass provides typed access and supplies defaults for
any key omitted from the YAML.  This makes every run fully reproducible
given the same YAML + pinned inputs.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from pensions_panorama.config import PARAMS_DIR

logger = logging.getLogger(__name__)


class ModelingAssumptions(BaseModel):
    """All global modeling assumptions for the pension engine.

    Values here mirror the OECD Pensions at a Glance methodology where
    feasible, and should be documented when they deviate.
    """

    # --- Career profile ---
    entry_age: int = Field(20, description="Age of labour-market entry.")
    career_length: int = Field(
        40,
        description="Total years of contributions (= retirement_age_male - entry_age by default).",
    )
    contribution_density: float = Field(
        1.0,
        description="Fraction of career with active contributions (0–1).",
    )

    # --- Retirement ages (used when country params defer to global default) ---
    default_retirement_age_male: int = Field(65, description="Default NRA for males.")
    default_retirement_age_female: int = Field(65, description="Default NRA for females.")

    # --- Wage trajectory ---
    real_wage_growth: float = Field(
        0.02,
        description="Annual real wage growth rate used for valorisation and projection.",
    )
    inflation: float = Field(
        0.02,
        description="Annual price inflation (used with valorisation = CPI).",
    )
    wage_growth: float | None = Field(
        None,
        description="Nominal wage growth; computed as real_wage_growth + inflation if None.",
    )

    # --- Present-value discount ---
    discount_rate: float = Field(
        0.02,
        description="Real annual discount rate for pension-wealth (PV) calculation.",
    )

    # --- Post-retirement indexation ---
    pension_indexation_type: str = Field(
        "CPI",
        description="Default indexation type: 'wages', 'CPI', 'mixed', 'none'.",
    )
    pension_indexation_rate: float = Field(
        0.0,
        description=(
            "Real post-retirement indexation rate. "
            "0.0 means pensions keep constant real value (i.e. CPI-indexed)."
        ),
    )

    # --- DC-specific ---
    dc_real_return_net_of_fees: float = Field(
        0.03,
        description="Annual real net-of-fees return for DC funds.",
    )

    # --- Life expectancy (fallback if UN data unavailable) ---
    life_expectancy_at_retirement_male: float = Field(
        20.0,
        description="Years of remaining life at male retirement age (fallback).",
    )
    life_expectancy_at_retirement_female: float = Field(
        25.0,
        description="Years of remaining life at female retirement age (fallback).",
    )
    max_age_for_wealth: int = Field(
        110,
        description="Maximum age used in survival-weighted pension-wealth sum.",
    )

    # --- Earnings multiples at which to evaluate ---
    earnings_multiples: list[float] = Field(
        default=[0.5, 0.75, 1.0, 1.5, 2.0, 2.5],
        description="Individual wages expressed as multiples of average wage.",
    )

    # --- Sex (default for modeling) ---
    sex: str = Field("male", description="Default modeling sex: 'male', 'female', 'total'.")

    # --- WPP reference year for life tables ---
    wpp_year: int = Field(
        2020,
        description="WPP quinquennial start year for UN life-table queries.",
    )

    def effective_wage_growth(self) -> float:
        return self.wage_growth if self.wage_growth is not None else (
            self.real_wage_growth + self.inflation
        )

    def life_expectancy_at_retirement(self, sex: str = "male") -> float:
        if sex.lower() in ("female", "f"):
            return self.life_expectancy_at_retirement_female
        return self.life_expectancy_at_retirement_male


def load_assumptions(
    filename: str = "assumptions.yaml",
    params_dir: Path | None = None,
    overrides: dict[str, Any] | None = None,
) -> ModelingAssumptions:
    """Load global assumptions from YAML, applying any run-level overrides.

    Parameters
    ----------
    filename:
        Name of the YAML file inside ``params_dir``.
    params_dir:
        Directory containing the file; defaults to ``data/params/``.
    overrides:
        Dict of key→value pairs that take precedence over the YAML.
    """
    directory = params_dir or PARAMS_DIR
    path = directory / filename

    raw: dict[str, Any] = {}
    if path.exists():
        with open(path) as fh:
            raw = yaml.safe_load(fh) or {}
        logger.info("Loaded modeling assumptions from %s", path)
    else:
        logger.warning("Assumptions file not found at %s; using defaults.", path)

    if overrides:
        raw.update(overrides)

    return ModelingAssumptions(**raw)
