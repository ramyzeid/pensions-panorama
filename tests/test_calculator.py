"""Tests for the personalised pension calculator (compute_benefit)."""

from __future__ import annotations

import warnings
from pathlib import Path

import pytest

from pensions_panorama.model.calculator import PersonProfile
from pensions_panorama.model.pension_engine import PensionEngine
from pensions_panorama.schema.params_schema import load_country_params


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_PARAMS_DIR = Path(__file__).parent.parent / "data" / "params"


@pytest.fixture(scope="module")
def jor_engine():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    from pensions_panorama.model.assumptions import load_assumptions
    params = load_country_params(_PARAMS_DIR / "JOR.yaml")
    assumptions = load_assumptions(params_dir=_PARAMS_DIR)
    return PensionEngine(
        country_params=params,
        assumptions=assumptions,
        average_wage=8880.0,
        survival_factor=16.5,
    )


@pytest.fixture(scope="module")
def mar_engine():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    from pensions_panorama.model.assumptions import load_assumptions
    params = load_country_params(_PARAMS_DIR / "MAR.yaml")
    assumptions = load_assumptions(params_dir=_PARAMS_DIR)
    return PensionEngine(
        country_params=params,
        assumptions=assumptions,
        average_wage=98748.0,
        survival_factor=16.0,
    )


# ---------------------------------------------------------------------------
# Eligibility boundary tests
# ---------------------------------------------------------------------------

def test_eligible_at_nra(jor_engine):
    """Person exactly at NRA with sufficient service is eligible."""
    person = PersonProfile(
        sex="male",
        age=60.0,
        service_years=25.0,
        wage=8880.0,
        wage_unit="currency",
        worker_type_id="private_employee",
    )
    result = jor_engine.compute_benefit(person)
    assert result.eligibility.is_eligible is True
    assert result.eligibility.missing == []
    assert result.gross_benefit > 0


def test_not_eligible_age(jor_engine):
    """Person below NRA → is_eligible=False, missing contains age info."""
    person = PersonProfile(
        sex="male",
        age=50.0,
        service_years=25.0,
        wage=8880.0,
        worker_type_id="private_employee",
    )
    result = jor_engine.compute_benefit(person)
    assert result.eligibility.is_eligible is False
    assert any("NRA" in m or "age" in m.lower() for m in result.eligibility.missing)


def test_not_eligible_service(jor_engine):
    """service_years < minimum → is_eligible=False, missing contains service info."""
    person = PersonProfile(
        sex="male",
        age=60.0,
        service_years=5.0,   # JOR requires 15 years minimum
        wage=8880.0,
        worker_type_id="private_employee",
    )
    result = jor_engine.compute_benefit(person)
    assert result.eligibility.is_eligible is False
    assert any("contribution" in m.lower() or "service" in m.lower() or "minimum" in m.lower()
               for m in result.eligibility.missing)


def test_excluded_worker_type(jor_engine):
    """coverage_status == excluded → gross_benefit == 0, warning present."""
    person = PersonProfile(
        sex="male",
        age=60.0,
        service_years=25.0,
        wage=8880.0,
        worker_type_id="military",
    )
    result = jor_engine.compute_benefit(person)
    assert result.gross_benefit == 0.0
    assert result.net_benefit == 0.0
    assert len(result.warnings) > 0
    assert any("excluded" in w.lower() for w in result.warnings)


def test_excluded_worker_type_eligibility_has_missing(jor_engine):
    """Excluded workers have is_eligible=False and a message in missing."""
    person = PersonProfile(
        sex="female",
        age=65.0,
        service_years=30.0,
        wage=8880.0,
        worker_type_id="domestic_worker",
    )
    result = jor_engine.compute_benefit(person)
    assert result.eligibility.is_eligible is False
    assert len(result.eligibility.missing) > 0


# ---------------------------------------------------------------------------
# Cross-country worker-type diff tests
# ---------------------------------------------------------------------------

def test_self_employed_vs_private_jor(jor_engine):
    """JOR: self_employed and private_employee at same wage produce valid results.

    Self-employed pays full combined rate; benefits should be the same since
    they access the same scheme.
    """
    wage = 8880.0

    person_pe = PersonProfile(
        sex="male", age=60.0, service_years=25.0,
        wage=wage, worker_type_id="private_employee",
    )
    person_se = PersonProfile(
        sex="male", age=60.0, service_years=25.0,
        wage=wage, worker_type_id="self_employed",
    )

    result_pe = jor_engine.compute_benefit(person_pe)
    result_se = jor_engine.compute_benefit(person_se)

    # Both should be eligible
    assert result_pe.eligibility.is_eligible is True
    assert result_se.eligibility.is_eligible is True

    # Benefits should both be positive
    assert result_pe.gross_benefit > 0
    assert result_se.gross_benefit > 0

    # Self-employed covers same schemes, so benefit should be approximately equal
    # (within a small tolerance since same formula applies)
    assert abs(result_pe.gross_benefit - result_se.gross_benefit) / result_pe.gross_benefit < 0.01


def test_civil_servant_excluded_mar(mar_engine):
    """MAR civil_servant (excluded) → benefit is 0 with warning."""
    person = PersonProfile(
        sex="male",
        age=63.0,
        service_years=30.0,
        wage=98748.0,
        worker_type_id="civil_servant",
    )
    result = mar_engine.compute_benefit(person)
    assert result.gross_benefit == 0.0
    assert len(result.warnings) > 0


# ---------------------------------------------------------------------------
# Benefit sanity checks
# ---------------------------------------------------------------------------

def test_gross_gte_net(jor_engine):
    """Gross benefit should always be ≥ net benefit."""
    person = PersonProfile(
        sex="male", age=60.0, service_years=25.0,
        wage=8880.0, worker_type_id="private_employee",
    )
    result = jor_engine.compute_benefit(person)
    assert result.gross_benefit >= result.net_benefit


def test_replacement_rate_positive(jor_engine):
    """Replacement rate should be positive for eligible workers."""
    person = PersonProfile(
        sex="male", age=60.0, service_years=25.0,
        wage=8880.0, worker_type_id="private_employee",
    )
    result = jor_engine.compute_benefit(person)
    assert result.gross_replacement_rate > 0
    assert result.net_replacement_rate >= 0


def test_reasoning_trace_not_empty(jor_engine):
    """Reasoning trace should contain at least some steps."""
    person = PersonProfile(
        sex="male", age=60.0, service_years=25.0,
        wage=8880.0, worker_type_id="private_employee",
    )
    result = jor_engine.compute_benefit(person)
    assert len(result.reasoning_trace) > 0
    labels = [step.label for step in result.reasoning_trace]
    assert any("wage" in l.lower() for l in labels)


def test_wage_unit_aw_multiple(jor_engine):
    """wage_unit='aw_multiple' with 1.0 should give same result as currency with avg_wage."""
    avg_wage = 8880.0
    person_currency = PersonProfile(
        sex="male", age=60.0, service_years=25.0,
        wage=avg_wage, wage_unit="currency",
        worker_type_id="private_employee",
    )
    person_aw = PersonProfile(
        sex="male", age=60.0, service_years=25.0,
        wage=1.0, wage_unit="aw_multiple",
        worker_type_id="private_employee",
    )
    r1 = jor_engine.compute_benefit(person_currency)
    r2 = jor_engine.compute_benefit(person_aw)
    assert abs(r1.gross_benefit - r2.gross_benefit) < 1.0  # within 1 currency unit
