"""Tests for WorkerType schema models, inheritance resolution, and validation."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from pathlib import Path

from pensions_panorama.schema.params_schema import (
    CountryParams,
    CoverageStatus,
    WorkerTypeRules,
    load_country_params,
)

_PARAMS_DIR = Path(__file__).parent.parent / "data" / "params"

# ---------------------------------------------------------------------------
# Helpers – minimal valid CountryParams dict
# ---------------------------------------------------------------------------

def _base_params(extra_worker_types: dict | None = None) -> dict:
    """Return a minimal valid raw CountryParams dict."""
    wt = {
        "private_employee": {
            "label": "Private sector employee",
            "coverage_status": "mandatory",
            "scheme_ids": ["SSC_OAI"],
            "source_citation": "Test citation.",
        },
        "self_employed": {
            "label": "Self-employed",
            "coverage_status": "voluntary",
            "scheme_ids": [],
            "source_citation": "Test citation.",
        },
    }
    if extra_worker_types:
        wt.update(extra_worker_types)

    return {
        "metadata": {
            "country_name": "Testland",
            "iso3": "TST",
            "currency": "Testlar",
            "currency_code": "TST",
            "reference_year": 2023,
        },
        "schemes": [
            {
                "scheme_id": "SSC_OAI",
                "name": "Test DB Scheme",
                "tier": "first",
                "type": "DB",
                "coverage": "private employees",
                "eligibility": {
                    "normal_retirement_age_male": {"value": 65, "source_citation": "Test"},
                    "normal_retirement_age_female": {"value": 62, "source_citation": "Test"},
                },
                "contributions": {
                    "employee_rate": {"value": 0.08, "source_citation": "Test"},
                    "employer_rate": {"value": 0.12, "source_citation": "Test"},
                },
                "benefits": {
                    "accrual_rate_per_year": {"value": 0.02, "source_citation": "Test"},
                },
            }
        ],
        "taxes": {
            "simplified_net_rate": {"value": 0.0, "source_citation": "Test"},
        },
        "average_earnings": {
            "manual_value": 10000.0,
            "source_citation": "Test",
        },
        "worker_types": wt,
    }


# ---------------------------------------------------------------------------
# test_worker_types_schema_valid_jor
# ---------------------------------------------------------------------------

def test_worker_types_schema_valid_jor():
    """JOR loads with worker_types; resolve private_employee returns correct scheme_ids."""
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        params = load_country_params(_PARAMS_DIR / "JOR.yaml")

    assert len(params.worker_types) > 0
    assert "private_employee" in params.worker_types
    assert "self_employed" in params.worker_types

    resolved = params.resolve_worker_type("private_employee")
    assert "SSC_OAI" in resolved.scheme_ids
    assert resolved.coverage_status == CoverageStatus.MANDATORY

    resolved_se = params.resolve_worker_type("self_employed")
    assert resolved_se.coverage_status == CoverageStatus.VOLUNTARY


# ---------------------------------------------------------------------------
# test_inheritance_resolution
# ---------------------------------------------------------------------------

def test_inheritance_resolution():
    """Civil servant inherits from private_employee and overrides NRA; fields merge correctly."""
    raw = _base_params(extra_worker_types={
        "civil_servant": {
            "label": "Civil servant",
            "coverage_status": "mandatory",
            "scheme_ids": ["SSC_OAI"],
            "source_citation": "Test",
            "inherit": "private_employee",
            "eligibility_override": {
                "normal_retirement_age_male": {"value": 60, "source_citation": "CSR Law"},
                "normal_retirement_age_female": {"value": 60, "source_citation": "CSR Law"},
                "minimum_contribution_years": {"value": 20, "source_citation": "CSR Law"},
            },
        }
    })
    params = CountryParams.model_validate(raw)

    resolved = params.resolve_worker_type("civil_servant")
    assert resolved.eligibility_override is not None
    nra_m = resolved.eligibility_override.normal_retirement_age_male
    assert nra_m is not None
    assert float(nra_m.value) == 60.0

    min_yrs = resolved.eligibility_override.minimum_contribution_years
    assert min_yrs is not None
    assert float(min_yrs.value) == 20.0

    # Label should come from child (not parent)
    assert resolved.label == "Civil servant"
    # scheme_ids should come from child
    assert "SSC_OAI" in resolved.scheme_ids


# ---------------------------------------------------------------------------
# test_self_employed_missing_fails
# ---------------------------------------------------------------------------

def test_self_employed_missing_fails():
    """CountryParams without self_employed key raises ValidationError."""
    raw = {
        "metadata": {
            "country_name": "Testland",
            "iso3": "TST",
            "currency": "Testlar",
            "currency_code": "TST",
            "reference_year": 2023,
        },
        "schemes": [
            {
                "scheme_id": "SSC_OAI",
                "name": "Test DB",
                "tier": "first",
                "type": "DB",
                "coverage": "all",
                "eligibility": {
                    "normal_retirement_age_male": {"value": 65, "source_citation": "Test"},
                    "normal_retirement_age_female": {"value": 62, "source_citation": "Test"},
                },
                "contributions": {
                    "employee_rate": {"value": 0.08, "source_citation": "Test"},
                },
                "benefits": {
                    "accrual_rate_per_year": {"value": 0.02, "source_citation": "Test"},
                },
            }
        ],
        "taxes": {
            "simplified_net_rate": {"value": 0.0, "source_citation": "Test"},
        },
        "average_earnings": {
            "manual_value": 10000.0,
            "source_citation": "Test",
        },
        "worker_types": {
            "private_employee": {
                "label": "Private sector employee",
                "coverage_status": "mandatory",
                "scheme_ids": ["SSC_OAI"],
                "source_citation": "Test",
            },
            # Missing self_employed!
        },
    }
    with pytest.raises(ValidationError, match="self_employed"):
        CountryParams.model_validate(raw)


# ---------------------------------------------------------------------------
# test_invalid_scheme_id_in_worker_type_fails
# ---------------------------------------------------------------------------

def test_invalid_scheme_id_in_worker_type_fails():
    """scheme_id not in schemes raises ValidationError."""
    raw = _base_params()
    raw["worker_types"]["private_employee"]["scheme_ids"] = ["NONEXISTENT_SCHEME"]

    with pytest.raises(ValidationError, match="NONEXISTENT_SCHEME"):
        CountryParams.model_validate(raw)


# ---------------------------------------------------------------------------
# test_circular_inheritance_fails
# ---------------------------------------------------------------------------

def test_circular_inheritance_fails():
    """A → B → A raises ValidationError."""
    raw = _base_params(extra_worker_types={
        "type_a": {
            "label": "Type A",
            "coverage_status": "mandatory",
            "scheme_ids": [],
            "source_citation": "Test",
            "inherit": "type_b",
        },
        "type_b": {
            "label": "Type B",
            "coverage_status": "mandatory",
            "scheme_ids": [],
            "source_citation": "Test",
            "inherit": "type_a",
        },
    })

    with pytest.raises(ValidationError, match="[Cc]ircular"):
        CountryParams.model_validate(raw)
