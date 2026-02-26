"""Shared pytest fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest
import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).parent.parent
PARAMS_DIR = PROJECT_ROOT / "data" / "params"


# ---------------------------------------------------------------------------
# Country parameter fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def jor_params():
    """Validated Jordan parameter object."""
    from pensions_panorama.schema.params_schema import load_country_params
    return load_country_params(PARAMS_DIR / "JOR.yaml")


@pytest.fixture
def mar_params():
    """Validated Morocco parameter object."""
    from pensions_panorama.schema.params_schema import load_country_params
    return load_country_params(PARAMS_DIR / "MAR.yaml")


@pytest.fixture
def default_assumptions():
    """Default global modeling assumptions."""
    from pensions_panorama.model.assumptions import load_assumptions
    return load_assumptions(params_dir=PARAMS_DIR)


@pytest.fixture
def jor_engine(jor_params, default_assumptions):
    """PensionEngine for Jordan with a fixed average wage."""
    from pensions_panorama.model.pension_engine import PensionEngine
    return PensionEngine(
        country_params=jor_params,
        assumptions=default_assumptions,
        average_wage=8880.0,  # JOD; ~JOD 740/month × 12
        survival_factor=16.5,  # Pre-computed fallback annuity factor
    )


@pytest.fixture
def mar_engine(mar_params, default_assumptions):
    """PensionEngine for Morocco with a fixed average wage."""
    from pensions_panorama.model.pension_engine import PensionEngine
    return PensionEngine(
        country_params=mar_params,
        assumptions=default_assumptions,
        average_wage=98748.0,  # MAD; HCP estimate
        survival_factor=16.0,
    )


# ---------------------------------------------------------------------------
# Mock API responses
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_wb_response():
    """Minimal paginated World Bank API response for CPI indicator."""
    return [
        {"page": 1, "pages": 1, "per_page": 1000, "total": 3, "sourceid": "2"},
        [
            {"countryiso3code": "JOR", "date": "2021", "value": 1.3,
             "indicator": {"id": "FP.CPI.TOTL.ZG", "value": "Inflation"}},
            {"countryiso3code": "JOR", "date": "2022", "value": 4.2,
             "indicator": {"id": "FP.CPI.TOTL.ZG", "value": "Inflation"}},
            {"countryiso3code": "JOR", "date": "2023", "value": 2.1,
             "indicator": {"id": "FP.CPI.TOTL.ZG", "value": "Inflation"}},
        ],
    ]


@pytest.fixture
def mock_survival_df():
    """Synthetic survival probability DataFrame for testing pension wealth."""
    import numpy as np
    ages = list(range(60, 101))
    # Exponential decay: S(t) = exp(-0.05 * t)
    t_vals = [a - 60 for a in ages]
    surv = [float(np.exp(-0.04 * t)) for t in t_vals]
    return pd.DataFrame({"t": t_vals, "age": ages, "survival_prob": surv})
