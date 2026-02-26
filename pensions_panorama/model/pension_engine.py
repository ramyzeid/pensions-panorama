"""Pension engine – computes gross pension entitlements for each scheme type.

Supported scheme types
----------------------
DB       – Defined-benefit (accrual-rate formula, career-average or final salary)
POINTS   – Points / notional-unit system
NDC      – Non-financial defined contribution
DC       – Financial defined contribution
BASIC    – Flat-rate basic / universal pension
TARGETED – Means-tested social pension (simplified phase-out)
MINIMUM  – Minimum-pension guarantee (applied as top-up in aggregate())

Architecture
------------
PensionEngine.compute(earnings_multiple) returns a PensionResult that contains:
  - gross and net annual pension amounts
  - gross and net replacement rates (relative to individual wage)
  - gross and net pension levels (relative to average wage)
  - gross and net pension wealth (multiples of average wage)
  - per-component breakdown dict

Pension wealth is computed here using a simplified annuity factor (fallback)
or delegated to pension_wealth.py when UN life-table data are available.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from pensions_panorama.model.assumptions import ModelingAssumptions
from pensions_panorama.schema.params_schema import (
    BenefitRules,
    ContributionRules,
    CountryParams,
    CoverageStatus,
    SchemeComponent,
    SchemeType,
    SourcedValue,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------

@dataclass
class PensionResult:
    """All indicators for one earnings multiple."""

    earnings_multiple: float
    individual_wage: float          # annual, national currency
    average_wage: float             # annual, national currency

    # Core output indicators
    gross_benefit: float            # annual gross pension
    net_benefit: float              # annual net pension

    gross_replacement_rate: float   # gross_benefit / individual_wage
    net_replacement_rate: float     # net_benefit  / individual_wage

    gross_pension_level: float      # gross_benefit / average_wage
    net_pension_level: float        # net_benefit   / average_wage

    gross_pension_wealth: float     # PV(gross) / average_wage
    net_pension_wealth: float       # PV(net)   / average_wage

    # Breakdown by scheme component (scheme_id → annual gross amount)
    component_breakdown: dict[str, float] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Helper: extract numeric value from SourcedValue
# ---------------------------------------------------------------------------

def _sv(sv: SourcedValue | None, default: float | None = None) -> float | None:
    if sv is None or sv.value is None:
        return default
    try:
        return float(sv.value)
    except (TypeError, ValueError):
        return default


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class PensionEngine:
    """Stateless pension calculator for one country.

    Parameters
    ----------
    country_params:
        Validated country parameter object (loaded from YAML).
    assumptions:
        Global modeling assumptions.
    average_wage:
        Annual average wage in national currency (from ILOSTAT or manual).
    survival_factor:
        Pre-computed annuity factor (sum of discounted survival probs).
        If None, a simplified life-expectancy-based annuity factor is used.
    """

    def __init__(
        self,
        country_params: CountryParams,
        assumptions: ModelingAssumptions,
        average_wage: float,
        survival_factor: float | None = None,
    ) -> None:
        self.params = country_params
        self.asmp = assumptions
        self.avg_wage = average_wage
        self._survival_factor = survival_factor

    # ------------------------------------------------------------------
    # Public entry points
    # ------------------------------------------------------------------

    def compute(
        self,
        earnings_multiple: float,
        sex: str | None = None,
    ) -> PensionResult:
        """Compute pension indicators for one earnings multiple.

        Parameters
        ----------
        earnings_multiple:
            Individual wage as a multiple of the average wage (e.g. 1.0).
        sex:
            ``"male"`` or ``"female"``; defaults to the assumption's sex field.
        """
        sex = (sex or self.asmp.sex).lower()
        individual_wage = earnings_multiple * self.avg_wage

        # --- Compute each active scheme's gross benefit ---
        breakdown: dict[str, float] = {}
        for scheme in self.params.schemes:
            if not scheme.active:
                continue
            benefit = self._dispatch(scheme, individual_wage, sex)
            breakdown[scheme.scheme_id] = max(0.0, benefit)

        # --- Aggregate: sum non-minimum schemes, then apply minimum guarantee ---
        gross_benefit = self._aggregate(breakdown)

        # --- Net benefit via tax engine ---
        net_benefit = self._apply_tax(gross_benefit, individual_wage)

        # --- Replacement rates ---
        grr = gross_benefit / individual_wage if individual_wage else 0.0
        nrr = net_benefit / individual_wage if individual_wage else 0.0

        # --- Pension levels (× AW) ---
        gpl = gross_benefit / self.avg_wage if self.avg_wage else 0.0
        npl = net_benefit / self.avg_wage if self.avg_wage else 0.0

        # --- Pension wealth ---
        af = self._annuity_factor(sex)
        gpw = gpl * af
        npw = npl * af

        return PensionResult(
            earnings_multiple=earnings_multiple,
            individual_wage=individual_wage,
            average_wage=self.avg_wage,
            gross_benefit=gross_benefit,
            net_benefit=net_benefit,
            gross_replacement_rate=grr,
            net_replacement_rate=nrr,
            gross_pension_level=gpl,
            net_pension_level=npl,
            gross_pension_wealth=gpw,
            net_pension_wealth=npw,
            component_breakdown=breakdown,
        )

    def run_all_multiples(
        self,
        earnings_multiples: list[float] | None = None,
        sex: str | None = None,
    ) -> list[PensionResult]:
        """Compute results for all configured earnings multiples."""
        multiples = earnings_multiples or self.asmp.earnings_multiples
        return [self.compute(m, sex=sex) for m in multiples]

    # ------------------------------------------------------------------
    # Aggregation
    # ------------------------------------------------------------------

    def _aggregate(self, breakdown: dict[str, float]) -> float:
        """Sum scheme benefits, applying minimum-guarantee top-up if needed."""
        main_total = 0.0
        min_guarantee = 0.0
        min_scheme_ids: list[str] = []

        for scheme in self.params.schemes:
            if not scheme.active:
                continue
            val = breakdown.get(scheme.scheme_id, 0.0)
            if scheme.type == SchemeType.MINIMUM:
                min_scheme_ids.append(scheme.scheme_id)
                min_guarantee = max(min_guarantee, val)
            else:
                main_total += val

        # Top-up: guarantee is activated only if main_total falls short
        if min_guarantee > main_total and min_scheme_ids:
            top_up = min_guarantee - main_total
            # Credit the top-up to the first minimum-guarantee scheme
            breakdown[min_scheme_ids[0]] = top_up
            for sid in min_scheme_ids[1:]:
                breakdown[sid] = 0.0
        else:
            for sid in min_scheme_ids:
                breakdown[sid] = 0.0

        return max(main_total, min_guarantee)

    # ------------------------------------------------------------------
    # Dispatch by scheme type
    # ------------------------------------------------------------------

    def _dispatch(
        self, scheme: SchemeComponent, wage: float, sex: str
    ) -> float:
        dispatch = {
            SchemeType.DB: self._compute_db,
            SchemeType.POINTS: self._compute_points,
            SchemeType.NDC: self._compute_ndc,
            SchemeType.DC: self._compute_dc,
            SchemeType.BASIC: self._compute_basic,
            SchemeType.TARGETED: self._compute_targeted,
            SchemeType.MINIMUM: self._compute_minimum,
        }
        fn = dispatch.get(scheme.type)
        if fn is None:
            logger.warning("Unsupported scheme type: %s", scheme.type)
            return 0.0
        return fn(scheme, wage, sex)

    # ------------------------------------------------------------------
    # Scheme-type calculators
    # ------------------------------------------------------------------

    def _compute_db(
        self, scheme: SchemeComponent, wage: float, sex: str
    ) -> float:
        """Defined-benefit accrual formula."""
        accrual = _sv(scheme.benefits.accrual_rate_per_year)
        if accrual is None:
            logger.warning("%s: accrual_rate_per_year missing.", scheme.scheme_id)
            return 0.0

        effective_years = self.asmp.career_length * self.asmp.contribution_density

        # Reference wage (base for benefit formula)
        ref_type = (scheme.benefits.reference_wage or "career_average").lower()
        valorization = (scheme.benefits.valorization or "wages").lower()

        if "career" in ref_type:
            if "wage" in valorization:
                # Career-average valorised to current wages ≈ final wage
                ref_wage = wage
            elif "cpi" in valorization:
                # Career-average with CPI valorisation: real value of past wages
                # Approximate: avg of wages earned uniformly over career, CPI-deflated
                # Half-career lag at inflation rate
                half_career = self.asmp.career_length / 2
                ref_wage = wage * (1 + self.asmp.inflation) ** (-half_career) * (
                    1 + self.asmp.inflation
                ) ** half_career  # simplifies to wage (flat real)
                ref_wage = wage  # flat real career avg when CPI-valorised
            else:
                ref_wage = wage
        elif "best" in ref_type:
            # Best-N-years: approximate as final salary (conservative)
            ref_wage = wage
        else:
            # Final salary
            ref_wage = wage

        # Cap reference wage if contribution ceiling applies
        if scheme.contributions:
            ceil_mult = _sv(scheme.contributions.contribution_ceiling_aw_multiple)
            if ceil_mult is not None:
                ref_wage = min(ref_wage, ceil_mult * self.avg_wage)

        gross = accrual * effective_years * ref_wage
        return self._apply_minmax(gross, scheme.benefits)

    def _compute_points(
        self, scheme: SchemeComponent, wage: float, sex: str
    ) -> float:
        """Points system: points = (wage / AW) × years; gross = points × point_value."""
        effective_years = self.asmp.career_length * self.asmp.contribution_density

        # Point value interpretation:
        # If < 1 → fraction of AW per point; if > 1 → absolute currency amount
        pv = _sv(scheme.benefits.point_value)
        if pv is None:
            # Derive from point_cost if available (point_value = cost if cost is in AW)
            pc = _sv(scheme.benefits.point_cost)
            pv = (pc * self.avg_wage) if pc is not None else (self.avg_wage * 0.01)

        # Points earned proportional to relative wage
        points = (wage / self.avg_wage) * effective_years

        # If point_value looks like a fraction of AW (< 5), treat it as ×AW
        if pv < 5:
            point_val_currency = pv * self.avg_wage
        else:
            point_val_currency = pv

        gross = points * point_val_currency
        return self._apply_minmax(gross, scheme.benefits)

    def _compute_ndc(
        self, scheme: SchemeComponent, wage: float, sex: str
    ) -> float:
        """Non-financial defined contribution (NDC)."""
        effective_years = self.asmp.career_length
        density = self.asmp.contribution_density
        contrib_rate = self._total_contrib_rate(scheme)

        # Notional interest rate
        rate_str = (scheme.benefits.notional_interest_rate or "wages").lower()
        if "wage" in rate_str:
            notional_rate = self.asmp.effective_wage_growth()
        elif "cpi" in rate_str:
            notional_rate = self.asmp.inflation
        else:
            try:
                notional_rate = float(rate_str.strip("%")) / 100
            except ValueError:
                notional_rate = self.asmp.real_wage_growth

        # FV of annuity of contributions growing at notional_rate for career_length years
        if notional_rate > 0:
            fv_factor = ((1 + notional_rate) ** effective_years - 1) / notional_rate
        else:
            fv_factor = effective_years

        notional_account = contrib_rate * wage * density * fv_factor

        # Annuity divisor
        divisor = _sv(scheme.benefits.annuity_divisor_at_nra)
        if divisor is None:
            # Fallback: remaining life expectancy at retirement
            divisor = self.asmp.life_expectancy_at_retirement(sex)

        gross = (notional_account / divisor) if divisor > 0 else 0.0
        return self._apply_minmax(gross, scheme.benefits)

    def _compute_dc(
        self, scheme: SchemeComponent, wage: float, sex: str
    ) -> float:
        """Financial defined contribution (DC)."""
        effective_years = self.asmp.career_length
        density = self.asmp.contribution_density
        contrib_rate = self._total_contrib_rate(scheme)
        real_return = self.asmp.dc_real_return_net_of_fees

        # FV of contributions at real net return
        if real_return > 0:
            fv_factor = ((1 + real_return) ** effective_years - 1) / real_return
        else:
            fv_factor = effective_years

        account = contrib_rate * wage * density * fv_factor

        # Convert to annuity
        le = self.asmp.life_expectancy_at_retirement(sex)
        discount = self.asmp.discount_rate

        if discount > 0:
            annuity_factor = (1 - (1 + discount) ** (-le)) / discount
        else:
            annuity_factor = le

        gross = (account / annuity_factor) if annuity_factor > 0 else 0.0
        return self._apply_minmax(gross, scheme.benefits)

    def _compute_basic(
        self, scheme: SchemeComponent, wage: float, sex: str
    ) -> float:
        """Universal flat-rate benefit."""
        # Try flat_rate_aw_multiple first, then flat_rate_absolute
        rate = _sv(scheme.benefits.flat_rate_aw_multiple)
        if rate is not None:
            return rate * self.avg_wage

        abs_rate = _sv(scheme.benefits.flat_rate_absolute)
        if abs_rate is not None:
            return abs_rate

        # Fallback: use minimum_benefit_aw_multiple as the flat rate
        min_mult = _sv(scheme.benefits.minimum_benefit_aw_multiple)
        if min_mult is not None:
            return min_mult * self.avg_wage

        logger.warning(
            "%s (basic): no flat_rate_aw_multiple or flat_rate_absolute defined.",
            scheme.scheme_id,
        )
        return 0.0

    def _compute_targeted(
        self, scheme: SchemeComponent, wage: float, sex: str
    ) -> float:
        """Means-tested (targeted) social pension with simplified phase-out.

        Full benefit is paid at zero individual income; linearly phased out
        as income rises.  The phase-out starts at 0 income and is complete
        at max_benefit / phase_out_rate above AW.

        This is a deliberate simplification.  A full means-test would require
        modelling income in retirement; here we proxy with the working wage.
        """
        max_mult = _sv(scheme.benefits.maximum_benefit_aw_multiple)
        max_abs = _sv(scheme.benefits.maximum_benefit_absolute)

        if max_mult is not None:
            max_benefit = max_mult * self.avg_wage
        elif max_abs is not None:
            max_benefit = max_abs
        else:
            min_mult = _sv(scheme.benefits.minimum_benefit_aw_multiple)
            max_benefit = (min_mult * self.avg_wage) if min_mult is not None else 0.0

        # Phase-out: benefit = max(0, max_benefit - 0.5 × wage above 0.5 AW)
        # (OECD-style social-assistance phase-out: 50 ppt taper rate)
        threshold = 0.0
        taper = 0.5
        excess = max(0.0, wage - threshold)
        benefit = max(0.0, max_benefit - taper * excess)
        return benefit

    def _compute_minimum(
        self, scheme: SchemeComponent, wage: float, sex: str
    ) -> float:
        """Minimum pension guarantee level (applied as top-up in aggregate)."""
        min_mult = _sv(scheme.benefits.minimum_benefit_aw_multiple)
        if min_mult is not None:
            return min_mult * self.avg_wage
        abs_min = _sv(scheme.benefits.minimum_benefit_absolute)
        if abs_min is not None:
            return abs_min
        return 0.0

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _apply_minmax(gross: float, benefits: BenefitRules) -> float:
        """Enforce minimum and maximum benefit constraints."""
        # We can't access avg_wage here without passing it, so the caller does that.
        # This static version takes only absolute values; relative versions handled in callers.
        return gross  # Constraints applied below via instance method

    def _apply_constraints(self, gross: float, benefits: BenefitRules) -> float:
        min_mult = _sv(benefits.minimum_benefit_aw_multiple)
        max_mult = _sv(benefits.maximum_benefit_aw_multiple)
        min_abs = _sv(benefits.minimum_benefit_absolute)
        max_abs = _sv(benefits.maximum_benefit_absolute)

        if min_mult is not None:
            gross = max(gross, min_mult * self.avg_wage)
        if min_abs is not None:
            gross = max(gross, min_abs)
        if max_mult is not None:
            gross = min(gross, max_mult * self.avg_wage)
        if max_abs is not None:
            gross = min(gross, max_abs)
        return gross

    def _apply_minmax(self, gross: float, benefits: BenefitRules) -> float:  # type: ignore[override]
        return self._apply_constraints(gross, benefits)

    @staticmethod
    def _total_contrib_rate(scheme: SchemeComponent) -> float:
        """Return total contribution rate (employee + employer) as a decimal."""
        c: ContributionRules | None = scheme.contributions
        if c is None:
            return 0.0
        total = _sv(c.total_rate)
        if total is not None:
            return total
        emp = _sv(c.employee_rate, 0.0) or 0.0
        er = _sv(c.employer_rate, 0.0) or 0.0
        return emp + er

    def _annuity_factor(self, sex: str) -> float:
        """Return the annuity factor (survival-weighted PV per unit of annual pension).

        Uses the pre-computed survival factor if available; otherwise falls
        back to a simplified closed-form annuity (see pension_wealth.py).
        """
        if self._survival_factor is not None:
            return self._survival_factor

        # Simplified: level annuity discounted at real discount rate
        le = self.asmp.life_expectancy_at_retirement(sex)
        r = self.asmp.discount_rate
        g = self.asmp.pension_indexation_rate  # real indexation above inflation

        # Real net discount rate for indexed pensions
        real_d = ((1 + r) / (1 + g) - 1) if g > 0 else r

        if real_d > 0:
            return (1 - (1 + real_d) ** (-le)) / real_d
        return le

    def _apply_tax(self, gross_benefit: float, individual_wage: float) -> float:
        """Compute net benefit after pensioner taxes and social contributions."""
        from pensions_panorama.model.tax_engine import SimpleTaxEngine

        engine = SimpleTaxEngine(self.params.taxes, self.avg_wage)
        return engine.net_pension(gross_benefit, individual_wage)

    # ------------------------------------------------------------------
    # Personalized calculator
    # ------------------------------------------------------------------

    def compute_benefit(
        self,
        person: "PersonProfile",  # type: ignore[name-defined]  # noqa: F821
        assumptions: ModelingAssumptions | None = None,
    ) -> "BenefitResult":  # type: ignore[name-defined]  # noqa: F821
        """Compute a personalised pension benefit for a specific person.

        Parameters
        ----------
        person:
            A PersonProfile describing the individual.
        assumptions:
            Optional override; falls back to self.asmp.

        Returns
        -------
        BenefitResult with full eligibility, benefit, and reasoning trace.
        """
        from pensions_panorama.model.calculator import (
            BenefitResult,
            EligibilityResult,
            PersonProfile,
            ReasoningStep,
        )

        asmp = assumptions or self.asmp
        warnings_list: list[str] = []
        trace: list[ReasoningStep] = []

        # 1. Resolve wage
        if person.wage_unit == "aw_multiple":
            individual_wage = person.wage * self.avg_wage
            trace.append(ReasoningStep(
                label="Reference wage",
                formula=f"{person.wage} × AW ({self.avg_wage:,.0f})",
                value=f"{self.params.metadata.currency_code} {individual_wage:,.0f}",
            ))
        else:
            individual_wage = person.wage
            trace.append(ReasoningStep(
                label="Reference wage",
                formula="Individual wage (provided)",
                value=f"{self.params.metadata.currency_code} {individual_wage:,.0f}",
            ))

        # 2. Resolve worker type
        wt_id = person.worker_type_id
        if self.params.worker_types and wt_id in self.params.worker_types:
            resolved_wt = self.params.resolve_worker_type(wt_id)
        else:
            resolved_wt = None
            if wt_id != "private_employee":
                warnings_list.append(
                    f"Worker type '{wt_id}' not found; using all active schemes."
                )

        # 3. If excluded, return zero benefit
        if resolved_wt is not None and resolved_wt.coverage_status == CoverageStatus.EXCLUDED:
            zero_elig = EligibilityResult(
                is_eligible=False,
                missing=[f"Worker type '{wt_id}' is excluded from this pension system."],
                normal_retirement_age=0.0,
                early_retirement_age=None,
                vesting_years=None,
                years_to_nra=0.0,
            )
            warnings_list.append(
                f"Worker type '{wt_id}' is excluded from mandatory pension coverage. "
                f"Benefit is zero. See notes: {resolved_wt.notes or ''}"
            )
            return BenefitResult(
                worker_type_id=wt_id,
                person=person,
                eligibility=zero_elig,
                gross_benefit=0.0,
                net_benefit=0.0,
                gross_replacement_rate=0.0,
                net_replacement_rate=0.0,
                gross_pension_level=0.0,
                net_pension_level=0.0,
                component_breakdown={},
                reasoning_trace=trace,
                warnings=warnings_list,
            )

        # 4. Determine applicable schemes
        sex = person.sex.lower()
        if resolved_wt is not None and resolved_wt.scheme_ids:
            applicable_schemes = [
                s for s in self.params.schemes
                if s.scheme_id in resolved_wt.scheme_ids and s.active
            ]
        else:
            applicable_schemes = [s for s in self.params.schemes if s.active]

        # 5. Determine retirement age & eligibility
        nra: float = 0.0
        era: float | None = None
        min_contrib_years: float | None = None
        vesting_yrs: float | None = None

        # Check worker-type eligibility override first
        el_override = resolved_wt.eligibility_override if resolved_wt else None
        if el_override:
            nra_sv = (
                el_override.normal_retirement_age_male if sex == "male"
                else el_override.normal_retirement_age_female
            )
            era_sv = (
                el_override.early_retirement_age_male if sex == "male"
                else el_override.early_retirement_age_female
            )
            if nra_sv and nra_sv.value is not None:
                nra = float(nra_sv.value)
            if era_sv and era_sv.value is not None:
                era = float(era_sv.value)
            if el_override.minimum_contribution_years and el_override.minimum_contribution_years.value is not None:
                min_contrib_years = float(el_override.minimum_contribution_years.value)
            if el_override.vesting_years and el_override.vesting_years.value is not None:
                vesting_yrs = float(el_override.vesting_years.value)

        # Fall back to first applicable scheme's eligibility
        if nra == 0.0 and applicable_schemes:
            first_elig = applicable_schemes[0].eligibility
            nra_sv = (
                first_elig.normal_retirement_age_male if sex == "male"
                else first_elig.normal_retirement_age_female
            )
            era_sv = (
                first_elig.early_retirement_age_male if sex == "male"
                else first_elig.early_retirement_age_female
            )
            if nra_sv and nra_sv.value is not None:
                nra = float(nra_sv.value)
            if era_sv and era_sv.value is not None:
                era = float(era_sv.value)
            if min_contrib_years is None and first_elig.minimum_contribution_years:
                v = first_elig.minimum_contribution_years.value
                if v is not None:
                    min_contrib_years = float(v)
            if vesting_yrs is None and first_elig.vesting_years:
                v = first_elig.vesting_years.value
                if v is not None:
                    vesting_yrs = float(v)

        contrib_years = person.contribution_years if person.contribution_years is not None else person.service_years

        # Build eligibility result
        missing: list[str] = []
        years_to_nra = nra - person.age
        if person.age < nra:
            missing.append(
                f"Age {person.age:.0f} < NRA {nra:.0f} "
                f"(need {years_to_nra:.1f} more year(s))"
            )
        if min_contrib_years is not None and contrib_years < min_contrib_years:
            deficit = min_contrib_years - contrib_years
            missing.append(
                f"Contribution years {contrib_years:.0f} < minimum {min_contrib_years:.0f} "
                f"(need {deficit:.1f} more)"
            )

        is_eligible = len(missing) == 0
        eligibility = EligibilityResult(
            is_eligible=is_eligible,
            missing=missing,
            normal_retirement_age=nra,
            early_retirement_age=era,
            vesting_years=vesting_yrs,
            years_to_nra=years_to_nra,
        )

        trace.append(ReasoningStep(
            label="Normal retirement age",
            formula=f"NRA ({sex})",
            value=str(nra),
        ))
        trace.append(ReasoningStep(
            label="Eligibility",
            formula="age >= NRA and service_years >= min_contribution_years",
            value="ELIGIBLE" if is_eligible else "NOT ELIGIBLE – " + "; ".join(missing),
        ))

        # 6. Early/late retirement multiplier
        retirement_multiplier = 1.0
        if person.age < nra and era is not None and person.age >= era:
            months_early = (nra - person.age) * 12
            penalty_per_month = 0.005  # 0.5%/month (default; SSC law notes)
            retirement_multiplier = max(0.0, 1.0 - penalty_per_month * months_early)
            trace.append(ReasoningStep(
                label="Early retirement adjustment",
                formula=f"1 - 0.5%/month × {months_early:.1f} months early",
                value=f"{retirement_multiplier:.4f}",
            ))

        # 7. Temporarily adjust assumptions for this person
        # Override career_length and contribution_density to match person's profile
        from pensions_panorama.model.assumptions import ModelingAssumptions
        import copy
        personal_asmp = copy.copy(asmp)
        personal_asmp = ModelingAssumptions(
            entry_age=asmp.entry_age,
            career_length=person.service_years,
            contribution_density=1.0,  # service_years already accounts for gaps
            real_wage_growth=asmp.real_wage_growth,
            inflation=asmp.inflation,
            discount_rate=asmp.discount_rate,
            dc_real_return_net_of_fees=asmp.dc_real_return_net_of_fees,
            pension_indexation_type=asmp.pension_indexation_type,
            pension_indexation_rate=asmp.pension_indexation_rate,
            earnings_multiples=asmp.earnings_multiples,
            sex=sex,
            wpp_year=asmp.wpp_year,
        )

        # Use a temporary engine with personal assumptions
        personal_engine = PensionEngine(
            country_params=self.params,
            assumptions=personal_asmp,
            average_wage=self.avg_wage,
            survival_factor=self._survival_factor,
        )

        # 8. Compute each applicable scheme
        breakdown: dict[str, float] = {}
        for scheme in applicable_schemes:
            gross_scheme = personal_engine._dispatch(scheme, individual_wage, sex)
            breakdown[scheme.scheme_id] = max(0.0, gross_scheme)
            trace.append(ReasoningStep(
                label=f"Scheme: {scheme.scheme_id}",
                formula=f"{scheme.type.value} formula",
                value=f"{self.params.metadata.currency_code} {breakdown[scheme.scheme_id]:,.0f}/yr",
                citation=scheme.benefits.accrual_rate_per_year.source_citation
                if scheme.benefits.accrual_rate_per_year else None,
            ))

        # Also include non-applicable minimum schemes for the full aggregate
        for scheme in self.params.schemes:
            if not scheme.active:
                continue
            if scheme.scheme_id not in breakdown and scheme.type == SchemeType.MINIMUM:
                # Only include minimum schemes that correspond to applicable schemes
                if resolved_wt is None or not resolved_wt.scheme_ids:
                    gross_scheme = personal_engine._dispatch(scheme, individual_wage, sex)
                    breakdown[scheme.scheme_id] = max(0.0, gross_scheme)

        # Build a per-scheme breakdown restricted to applicable + minimum
        gross_benefit = personal_engine._aggregate(breakdown)
        gross_benefit *= retirement_multiplier

        # 9. Net benefit
        net_benefit = self._apply_tax(gross_benefit, individual_wage)

        # 10. Rates
        grr = gross_benefit / individual_wage if individual_wage else 0.0
        nrr = net_benefit / individual_wage if individual_wage else 0.0
        gpl = gross_benefit / self.avg_wage if self.avg_wage else 0.0
        npl = net_benefit / self.avg_wage if self.avg_wage else 0.0

        trace.append(ReasoningStep(
            label="Gross pension",
            formula="sum of scheme benefits × retirement multiplier",
            value=f"{self.params.metadata.currency_code} {gross_benefit:,.0f}/yr "
                  f"({grr * 100:.1f}% RR)",
        ))
        trace.append(ReasoningStep(
            label="Net pension",
            formula=f"gross × (1 - effective tax rate)",
            value=f"{self.params.metadata.currency_code} {net_benefit:,.0f}/yr "
                  f"({nrr * 100:.1f}% RR)",
        ))

        return BenefitResult(
            worker_type_id=wt_id,
            person=person,
            eligibility=eligibility,
            gross_benefit=gross_benefit,
            net_benefit=net_benefit,
            gross_replacement_rate=grr,
            net_replacement_rate=nrr,
            gross_pension_level=gpl,
            net_pension_level=npl,
            component_breakdown=breakdown,
            reasoning_trace=trace,
            warnings=warnings_list,
        )
