"""Tests for the pension engine and pension-wealth calculator."""

from __future__ import annotations

import math
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent


class TestPensionEngineJordan:
    """End-to-end engine tests for Jordan (DB + minimum guarantee)."""

    def test_results_length(self, jor_engine, default_assumptions):
        results = jor_engine.run_all_multiples(default_assumptions.earnings_multiples)
        assert len(results) == len(default_assumptions.earnings_multiples)

    def test_earnings_multiples_correct(self, jor_engine, default_assumptions):
        results = jor_engine.run_all_multiples(default_assumptions.earnings_multiples)
        for r, m in zip(results, default_assumptions.earnings_multiples):
            assert abs(r.earnings_multiple - m) < 1e-9

    def test_individual_wage_proportional_to_average(self, jor_engine):
        r = jor_engine.compute(1.0)
        assert abs(r.individual_wage - jor_engine.avg_wage) < 1.0

    def test_gross_benefit_positive(self, jor_engine):
        results = jor_engine.run_all_multiples()
        for r in results:
            assert r.gross_benefit >= 0

    def test_net_benefit_le_gross(self, jor_engine):
        """Net benefit must not exceed gross benefit."""
        results = jor_engine.run_all_multiples()
        for r in results:
            assert r.net_benefit <= r.gross_benefit + 1e-9

    def test_replacement_rate_range(self, jor_engine):
        """Gross replacement rate should be between 0 and 100% for reasonable inputs."""
        results = jor_engine.run_all_multiples()
        for r in results:
            assert 0.0 <= r.gross_replacement_rate <= 1.5, (
                f"Unexpected GRR {r.gross_replacement_rate:.4f} at {r.earnings_multiple}×AW"
            )

    def test_pension_level_positive(self, jor_engine):
        results = jor_engine.run_all_multiples()
        for r in results:
            assert r.gross_pension_level >= 0

    def test_replacement_rate_decreasing_with_earnings(self, jor_engine):
        """For a DB scheme with ceiling, GRR should decrease (or flat) as earnings rise."""
        results = jor_engine.run_all_multiples([0.5, 1.0, 2.0])
        grr = [r.gross_replacement_rate for r in results]
        # At least the highest earner should have a lower or equal RR than 1.0×AW
        # (because minimum guarantee is less relevant at high earnings)
        assert grr[-1] <= grr[0] + 0.01  # allow small rounding

    def test_minimum_pension_guarantee_applies_at_low_earnings(self, jor_engine):
        """At very low earnings, the minimum guarantee should top up the DB formula."""
        low_result = jor_engine.compute(0.3)
        high_result = jor_engine.compute(2.0)
        # Low earner should have higher replacement rate due to minimum guarantee
        assert low_result.gross_replacement_rate >= high_result.gross_replacement_rate

    def test_component_breakdown_sums_to_gross(self, jor_engine):
        """Sum of component breakdown should equal total gross_benefit."""
        results = jor_engine.run_all_multiples()
        for r in results:
            breakdown_sum = sum(r.component_breakdown.values())
            assert abs(breakdown_sum - r.gross_benefit) < 0.01, (
                f"Breakdown sum {breakdown_sum:.4f} ≠ gross {r.gross_benefit:.4f}"
            )

    def test_pension_wealth_positive(self, jor_engine):
        results = jor_engine.run_all_multiples()
        for r in results:
            assert r.gross_pension_wealth >= 0
            assert r.net_pension_wealth >= 0

    def test_net_pension_wealth_le_gross(self, jor_engine):
        results = jor_engine.run_all_multiples()
        for r in results:
            assert r.net_pension_wealth <= r.gross_pension_wealth + 1e-9


class TestPensionEngineMorocco:
    """Spot-check engine for Morocco (DB with contribution ceiling)."""

    def test_mar_runs_without_error(self, mar_engine, default_assumptions):
        results = mar_engine.run_all_multiples(default_assumptions.earnings_multiples)
        assert len(results) == 6

    def test_mar_ceiling_caps_high_earner_benefit(self, mar_engine):
        """Workers above the contribution ceiling should not receive proportionally higher pensions."""
        r_low = mar_engine.compute(0.5)
        r_high = mar_engine.compute(2.5)
        # High earner's replacement rate should be lower due to ceiling
        assert r_high.gross_replacement_rate <= r_low.gross_replacement_rate + 0.01

    def test_mar_net_lower_than_gross(self, mar_engine):
        """Morocco has a positive effective tax rate (8%)."""
        r = mar_engine.compute(1.0)
        assert r.net_benefit < r.gross_benefit


class TestDBFormulaMath:
    """Unit tests for the DB formula arithmetic."""

    def _make_engine(self, accrual: float, avg_wage: float, career: int = 40,
                     density: float = 1.0, min_mult: float | None = None):
        from pensions_panorama.schema.params_schema import (
            CountryParams, CountryMetadata, SchemeComponent, SchemeTier,
            SchemeType, EligibilityRules, BenefitRules, ContributionRules,
            TaxAndContrib, AverageEarnings, SourcedValue,
        )
        from pensions_panorama.model.pension_engine import PensionEngine
        from pensions_panorama.model.assumptions import ModelingAssumptions

        def _sv(v):
            return SourcedValue(value=v, source_citation="Unit test")

        benefits = BenefitRules(
            accrual_rate_per_year=_sv(accrual),
            reference_wage="career_average",
            valorization="wages",
            indexation="CPI",
            minimum_benefit_aw_multiple=_sv(min_mult) if min_mult else None,
        )
        scheme = SchemeComponent(
            scheme_id="TEST_DB",
            name="Test DB",
            tier=SchemeTier.FIRST,
            type=SchemeType.DB,
            coverage="all",
            eligibility=EligibilityRules(
                normal_retirement_age_male=_sv(65),
                normal_retirement_age_female=_sv(65),
            ),
            contributions=ContributionRules(
                employee_rate=_sv(0.08),
                source_citation="test",
            ),
            benefits=benefits,
        )
        params = CountryParams(
            metadata=CountryMetadata(
                country_name="Testland",
                iso3="TST",
                currency="Test Dollar",
                currency_code="TSD",
                reference_year=2023,
            ),
            schemes=[scheme],
            taxes=TaxAndContrib(),
            average_earnings=AverageEarnings(
                manual_value=avg_wage,
                source_citation="unit test",
            ),
        )
        asmp = ModelingAssumptions(
            career_length=career,
            contribution_density=density,
            discount_rate=0.02,
            pension_indexation_rate=0.0,
            life_expectancy_at_retirement_male=20.0,
        )
        return PensionEngine(params, asmp, avg_wage, survival_factor=20.0)

    def test_db_exact_formula(self):
        """Gross = accrual_rate × career_length × wage for career_average valorised to wages."""
        engine = self._make_engine(accrual=0.02, avg_wage=10000, career=40, density=1.0)
        r = engine.compute(1.0)
        expected_gross = 0.02 * 40 * 10000  # = 8000
        assert abs(r.gross_benefit - expected_gross) < 1.0

    def test_db_replacement_rate_formula(self):
        engine = self._make_engine(accrual=0.02, avg_wage=10000, career=40)
        r = engine.compute(1.0)
        expected_grr = 0.02 * 40  # = 0.80 (80%)
        assert abs(r.gross_replacement_rate - expected_grr) < 0.01

    def test_pension_level_equals_gross_divided_by_aw(self):
        engine = self._make_engine(accrual=0.02, avg_wage=10000, career=40)
        r = engine.compute(1.5)
        expected_gpl = r.gross_benefit / engine.avg_wage
        assert abs(r.gross_pension_level - expected_gpl) < 1e-9

    def test_pension_wealth_formula(self):
        """PW = (gross / AW) × annuity_factor."""
        sf = 18.0  # pre-set survival factor
        engine = self._make_engine(accrual=0.02, avg_wage=10000, career=40)
        engine._survival_factor = sf
        r = engine.compute(1.0)
        expected_gpw = (r.gross_benefit / engine.avg_wage) * sf
        assert abs(r.gross_pension_wealth - expected_gpw) < 1e-9

    def test_density_reduces_benefit(self):
        """Lower contribution density → lower effective years → lower benefit."""
        engine_full = self._make_engine(accrual=0.02, avg_wage=10000, career=40, density=1.0)
        engine_half = self._make_engine(accrual=0.02, avg_wage=10000, career=40, density=0.5)
        r_full = engine_full.compute(1.0)
        r_half = engine_half.compute(1.0)
        assert r_half.gross_benefit < r_full.gross_benefit

    def test_minimum_guarantee_top_up(self):
        """Minimum guarantee tops up when DB formula yields below minimum."""
        # At 0.2×AW: DB = 0.02 × 40 × 0.2×AW = 0.16×AW → below minimum of 0.25
        engine = self._make_engine(accrual=0.02, avg_wage=10000, career=40, min_mult=0.25)
        r = engine.compute(0.2)
        # Gross should be at least minimum
        assert r.gross_benefit >= 0.25 * engine.avg_wage - 0.01

    def test_no_negative_benefits(self):
        engine = self._make_engine(accrual=0.02, avg_wage=10000, career=40)
        for m in [0.1, 0.5, 1.0, 2.0, 5.0]:
            r = engine.compute(m)
            assert r.gross_benefit >= 0
            assert r.net_benefit >= 0


class TestBasicPension:
    """Test flat-rate / basic pension type."""

    def _make_basic_engine(self, flat_rate_aw: float, avg_wage: float):
        from pensions_panorama.schema.params_schema import (
            CountryParams, CountryMetadata, SchemeComponent, SchemeTier,
            SchemeType, EligibilityRules, BenefitRules, TaxAndContrib,
            AverageEarnings, SourcedValue,
        )
        from pensions_panorama.model.pension_engine import PensionEngine
        from pensions_panorama.model.assumptions import ModelingAssumptions

        def _sv(v):
            return SourcedValue(value=v, source_citation="Test")

        scheme = SchemeComponent(
            scheme_id="BASIC",
            name="Basic Pension",
            tier=SchemeTier.FIRST,
            type=SchemeType.BASIC,
            coverage="all residents",
            eligibility=EligibilityRules(
                normal_retirement_age_male=_sv(65),
                normal_retirement_age_female=_sv(65),
            ),
            benefits=BenefitRules(flat_rate_aw_multiple=_sv(flat_rate_aw)),
        )
        params = CountryParams(
            metadata=CountryMetadata(
                country_name="Flatland",
                iso3="FLT",
                currency="Flat",
                currency_code="FLT",
                reference_year=2023,
            ),
            schemes=[scheme],
            taxes=TaxAndContrib(),
            average_earnings=AverageEarnings(
                manual_value=avg_wage,
                source_citation="test",
            ),
        )
        asmp = ModelingAssumptions(
            career_length=40,
            life_expectancy_at_retirement_male=20.0,
            discount_rate=0.02,
        )
        return PensionEngine(params, asmp, avg_wage, survival_factor=20.0)

    def test_basic_flat_rate(self):
        """Basic pension = flat_rate × avg_wage regardless of individual earnings."""
        engine = self._make_basic_engine(0.15, 10000)
        for m in [0.5, 1.0, 2.0]:
            r = engine.compute(m)
            assert abs(r.gross_benefit - 0.15 * 10000) < 1.0

    def test_basic_replacement_rate_varies_with_earnings(self):
        """RR = flat_amount / individual_wage → higher earners have lower RR."""
        engine = self._make_basic_engine(0.15, 10000)
        r_low = engine.compute(0.5)
        r_high = engine.compute(2.0)
        assert r_low.gross_replacement_rate > r_high.gross_replacement_rate


class TestTaxEngine:
    """Unit tests for the tax engine."""

    def test_simplified_zero_rate(self):
        from pensions_panorama.model.tax_engine import SimpleTaxEngine
        from pensions_panorama.schema.params_schema import TaxAndContrib, SourcedValue

        taxes = TaxAndContrib(
            simplified_net_rate=SourcedValue(value=0.0, source_citation="test")
        )
        engine = SimpleTaxEngine(taxes, average_wage=10000)
        assert abs(engine.net_pension(5000, 10000) - 5000) < 1e-9

    def test_simplified_nonzero_rate(self):
        from pensions_panorama.model.tax_engine import SimpleTaxEngine
        from pensions_panorama.schema.params_schema import TaxAndContrib, SourcedValue

        taxes = TaxAndContrib(
            simplified_net_rate=SourcedValue(value=0.08, source_citation="test")
        )
        engine = SimpleTaxEngine(taxes, average_wage=10000)
        expected = 5000 * 0.92
        assert abs(engine.net_pension(5000, 10000) - expected) < 1e-9

    def test_bracket_engine_progressive(self):
        from pensions_panorama.model.tax_engine import BracketTaxEngine
        brackets = [(20_000, 0.10), (50_000, 0.20), (float("inf"), 0.30)]
        engine = BracketTaxEngine(brackets, basic_allowance=5_000)
        # Taxable = 30000 - 5000 = 25000; tax = 20000*0.10 + 5000*0.20 = 2000+1000 = 3000
        net = engine.net_pension(30_000, 50_000)
        expected = 30_000 - 3_000
        assert abs(net - expected) < 1.0

    def test_bracket_effective_rate_increases_with_income(self):
        from pensions_panorama.model.tax_engine import BracketTaxEngine
        brackets = [(30_000, 0.10), (float("inf"), 0.30)]
        engine = BracketTaxEngine(brackets)
        rate_low = engine.effective_rate(10_000, 20_000)
        rate_high = engine.effective_rate(100_000, 100_000)
        assert rate_high > rate_low
