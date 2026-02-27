"""Pension wealth calculation: survival-weighted present value.

This module implements the OECD Pensions at a Glance methodology for
computing pension wealth as the expected present value of the benefit
stream, weighted by conditional survival probabilities from UN WPP life tables.

Pension wealth (PW) formula
---------------------------
PW = P₀ × Σ_{t=0}^{T-R} S(R+t|R) × [(1+g)/(1+d)]^t

where:
  P₀  = annual gross (or net) pension at retirement
  R   = retirement age
  T   = maximum age (e.g. 110)
  S(a|R) = lx(a) / lx(R)   – conditional survival prob to age a given alive at R
  g   = annual pension indexation rate
  d   = nominal discount rate  (= real rate + inflation if using nominal)

Pension wealth as a multiple of average wage = PW / AW.

When UN life-table data are unavailable, the module falls back to a
simplified closed-form annuity based on assumed life expectancy.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from pensions_panorama.model.assumptions import ModelingAssumptions

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Core computation
# ---------------------------------------------------------------------------

def compute_annuity_factor(
    survival_probs: pd.DataFrame,
    discount_rate: float,
    indexation_rate: float = 0.0,
    max_years: int | None = None,
) -> float:
    """Compute the survival-weighted annuity factor.

    Parameters
    ----------
    survival_probs:
        DataFrame with columns ``t`` (years since retirement) and
        ``survival_prob`` (conditional probability of surviving t years given
        alive at retirement).  Produced by
        ``UNDataPortalClient.get_survival_probabilities()``.
    discount_rate:
        Real annual discount rate.
    indexation_rate:
        Real annual pension indexation rate (0.0 = constant real value).
    max_years:
        Optionally cap the number of years summed.

    Returns
    -------
    float
        Annuity factor: PW per unit of annual pension.
    """
    if survival_probs.empty or "t" not in survival_probs.columns:
        return 0.0

    df = survival_probs.copy()
    if max_years is not None:
        df = df[df["t"] <= max_years]

    # Effective real net discount rate for indexed benefits
    # [(1+g)/(1+d)]^t compounding factor
    net_discount_factor = (1.0 + indexation_rate) / (1.0 + discount_rate)

    t_vals = df["t"].values.astype(float)
    s_vals = df["survival_prob"].values.astype(float)

    # Weights: survival × discount
    weights = s_vals * (net_discount_factor ** t_vals)
    annuity_factor = float(np.sum(weights))

    logger.debug(
        "Annuity factor: %.4f (d=%.3f g=%.3f T=%d)",
        annuity_factor,
        discount_rate,
        indexation_rate,
        int(t_vals.max()) if len(t_vals) > 0 else 0,
    )
    return annuity_factor


def fallback_annuity_factor(
    life_expectancy: float,
    discount_rate: float,
    indexation_rate: float = 0.0,
) -> float:
    """Simplified closed-form annuity factor when life tables are unavailable.

    Assumes constant survival probability (i.e. level annuity over life
    expectancy).  This overstates the annuity relative to the survival-
    weighted version since it ignores mortality.  Use only as a fallback.
    """
    real_d = ((1.0 + discount_rate) / (1.0 + indexation_rate)) - 1.0

    if abs(real_d) < 1e-9:
        return life_expectancy
    return (1.0 - (1.0 + real_d) ** (-life_expectancy)) / real_d


# ---------------------------------------------------------------------------
# High-level wrapper
# ---------------------------------------------------------------------------

class PensionWealthCalculator:
    """Computes pension wealth for a country using UN life tables when available.

    Usage
    -----
    calc = PensionWealthCalculator(assumptions, iso3="JOR", un_client=client)
    af = calc.annuity_factor(sex="male")
    gpw = gross_pension / avg_wage * af
    """

    def __init__(
        self,
        assumptions: ModelingAssumptions,
        iso3: str,
        un_client: "UNDataPortalClient | None" = None,  # type: ignore[name-defined]  # noqa: F821
    ) -> None:
        self.asmp = assumptions
        self.iso3 = iso3
        self._un = un_client
        self._cache: dict[tuple[str, int], float] = {}

    def annuity_factor(
        self,
        sex: str = "male",
        retirement_age: int | None = None,
    ) -> float:
        """Return the annuity factor for the given sex and retirement age.

        Tries UN life-table data first; falls back to simplified formula.
        """
        sex_norm = sex.lower()
        ret_age = retirement_age or (
            self.asmp.default_retirement_age_male
            if sex_norm == "male"
            else self.asmp.default_retirement_age_female
        )
        cache_key = (sex_norm, ret_age)

        if cache_key in self._cache:
            return self._cache[cache_key]

        af = self._compute_from_life_table(sex_norm, ret_age)
        if af is None or af <= 0:
            af = self._compute_fallback(sex_norm)
            logger.info(
                "%s: Using fallback annuity factor %.4f (sex=%s ret_age=%d)",
                self.iso3,
                af,
                sex_norm,
                ret_age,
            )
        else:
            logger.info(
                "%s: UN life-table annuity factor %.4f (sex=%s ret_age=%d)",
                self.iso3,
                af,
                sex_norm,
                ret_age,
            )

        self._cache[cache_key] = af
        return af

    def _compute_from_life_table(
        self, sex: str, retirement_age: int
    ) -> float | None:
        if self._un is None:
            return None

        try:
            survival = self._un.get_survival_probabilities(
                iso3=self.iso3,
                retirement_age=retirement_age,
                max_age=self.asmp.max_age_for_wealth,
                year=self.asmp.wpp_year,
                sex=sex,
            )
        except Exception as exc:
            logger.warning(
                "UN life-table fetch failed for %s sex=%s: %s", self.iso3, sex, exc
            )
            return None

        if survival.empty:
            return None

        return compute_annuity_factor(
            survival_probs=survival,
            discount_rate=self.asmp.discount_rate,
            indexation_rate=self.asmp.pension_indexation_rate,
        )

    def _compute_fallback(self, sex: str) -> float:
        le = self.asmp.life_expectancy_at_retirement(sex)
        return fallback_annuity_factor(
            life_expectancy=le,
            discount_rate=self.asmp.discount_rate,
            indexation_rate=self.asmp.pension_indexation_rate,
        )

    def compute_pension_wealth(
        self,
        annual_pension: float,
        average_wage: float,
        sex: str = "male",
        retirement_age: int | None = None,
    ) -> float:
        """Return pension wealth as a multiple of average wage.

        Parameters
        ----------
        annual_pension:
            Annual pension amount (gross or net, national currency).
        average_wage:
            Annual average wage (national currency).
        """
        if average_wage <= 0:
            return 0.0
        af = self.annuity_factor(sex=sex, retirement_age=retirement_age)
        return (annual_pension / average_wage) * af

    def compute_for_results(
        self,
        results: list,  # list[PensionResult]
        average_wage: float,
        sex: str = "male",
        retirement_age: int | None = None,
    ) -> None:
        """Update pension_wealth fields in a list of PensionResult objects in-place."""
        af = self.annuity_factor(sex=sex, retirement_age=retirement_age)
        for r in results:
            if average_wage > 0:
                r.gross_pension_wealth = (r.gross_benefit / average_wage) * af
                r.net_pension_wealth = (r.net_benefit / average_wage) * af
            else:
                r.gross_pension_wealth = 0.0
                r.net_pension_wealth = 0.0


# ---------------------------------------------------------------------------
# OECD-style work incentive indicator (60 → 65)
# ---------------------------------------------------------------------------

def compute_work_incentive_6065(
    iso3: str,
    params: "CountryParams",
    assumptions: "ModelingAssumptions",
    avg_wage: float,
    sex: str = "male",
    un_client: object | None = None,
) -> dict | None:
    """OECD-style annualised gross pension wealth change from ages 60 to 65.

    Bar = (PW60(65) - PW60(60)) / 5 × 100  [% of avg wage, annualised].
    Negative → implicit penalty for delaying past 60.
    Positive → incentive to delay claiming.

    Also computes an "own NRA" variant using (NRA-5 → NRA) window.

    Returns None on fatal error; dict with error key on non-fatal errors.
    """
    from pensions_panorama.model.calculator import PersonProfile
    from pensions_panorama.model.pension_engine import PensionEngine

    r = assumptions.discount_rate  # 0.02

    # Determine NRA for own-NRA variant
    nra = 65
    first_scheme = params.schemes[0] if params.schemes else None
    if first_scheme and first_scheme.eligibility:
        attr = "normal_retirement_age_male" if sex == "male" else "normal_retirement_age_female"
        sv = getattr(first_scheme.eligibility, attr, None)
        if sv and getattr(sv, "value", None) is not None:
            nra = int(sv.value)

    nra_minus5 = max(nra - 5, 50)
    ages_to_eval = sorted({60, 65, nra_minus5, nra})

    engine = PensionEngine(params, assumptions, avg_wage)
    pw_calc = PensionWealthCalculator(assumptions, iso3, un_client=un_client)

    pw60: dict[int, float] = {}
    for R in ages_to_eval:
        service_yrs = max(0.0, float(R - 20))
        person = PersonProfile(
            sex=sex,
            age=float(R),
            service_years=service_yrs,
            wage=1.0,
            wage_unit="aw_multiple",
            worker_type_id="private_employee",
        )
        try:
            B_R = engine.compute_benefit(person).gross_benefit
        except Exception:
            B_R = 0.0

        # AF(R) via UN WPP life table (or fallback inside pw_calc)
        AF_R = pw_calc.annuity_factor(sex=sex, retirement_age=R)

        # Survival from age 60 to R: p(60→R) = lx(R) / lx(60)
        if R <= 60:
            p_60_R = 1.0
        elif un_client is not None:
            try:
                surv = un_client.get_survival_probabilities(
                    iso3=iso3,
                    retirement_age=60,
                    max_age=R,
                    year=assumptions.wpp_year,
                    sex=sex,
                )
                row = surv[surv["t"] == (R - 60)]
                p_60_R = float(row["survival_prob"].iloc[0]) if not row.empty else 1.0
            except Exception:
                p_60_R = 1.0
        else:
            p_60_R = 1.0  # fallback: ignore pre-retirement mortality

        pw60[R] = (B_R * AF_R / ((1 + r) ** (R - 60)) * p_60_R / avg_wage) if avg_wage > 0 else 0.0

    bar_oecd = (pw60.get(65, 0.0) - pw60.get(60, 0.0)) / 5 * 100
    bar_own  = (pw60.get(nra, 0.0) - pw60.get(nra_minus5, 0.0)) / 5 * 100

    return {
        "PW60_60":        pw60.get(60, 0.0),
        "PW60_65":        pw60.get(65, 0.0),
        "bar_oecd":       bar_oecd,
        "nra":            nra,
        "nra_minus5":     nra_minus5,
        "PW60_nra":       pw60.get(nra, 0.0),
        "PW60_nra_m5":    pw60.get(nra_minus5, 0.0),
        "bar_own_nra":    bar_own,
        "mortality_source": "UN WPP" if un_client is not None else "fallback",
        "r":   r,
        "sex": sex,
    }
