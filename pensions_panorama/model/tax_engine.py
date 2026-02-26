"""Tax engine – computes net-of-tax pension benefit.

Architecture
------------
SimpleTaxEngine  – uses the simplified_net_rate field from the country YAML.
                   Net = gross × (1 − effective_rate).  This is the default
                   and appropriate when full tax-schedule data are unavailable.

BracketTaxEngine – full progressive income-tax schedule.  Instantiate with a
                   list of (upper_bound, rate) pairs and an optional basic
                   allowance.  Each country module can supply these.

ExtensionProtocol (abc) – interface for future country-specific modules.

The pension_engine always calls SimpleTaxEngine.  To upgrade a country to
BracketTaxEngine, set simplified_net_rate: null in the YAML and override
tax_engine() in a country-specific module under pensions_panorama/countries/.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod

from pensions_panorama.schema.params_schema import TaxAndContrib

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------

class TaxEngineBase(ABC):
    """Interface contract for all tax engines."""

    @abstractmethod
    def net_pension(self, gross_pension: float, individual_wage: float) -> float:
        """Return net annual pension after taxes and social contributions."""
        ...

    @abstractmethod
    def effective_rate(self, gross_pension: float, individual_wage: float) -> float:
        """Return the effective combined tax + social-contribution rate."""
        ...


# ---------------------------------------------------------------------------
# Simple (flat effective rate)
# ---------------------------------------------------------------------------

class SimpleTaxEngine(TaxEngineBase):
    """Applies a flat effective tax + social-contribution rate to pension income.

    Parameters
    ----------
    tax_rules:
        The TaxAndContrib object from the country parameter file.
    average_wage:
        Annual average wage (used for allowance calculations if needed).
    """

    def __init__(self, tax_rules: TaxAndContrib, average_wage: float) -> None:
        self._rules = tax_rules
        self._avg_wage = average_wage
        self._flat_rate = self._resolve_rate()

    def _resolve_rate(self) -> float:
        snr = self._rules.simplified_net_rate
        if snr is not None and snr.value is not None:
            try:
                rate = float(snr.value)
                if not (0.0 <= rate <= 1.0):
                    logger.warning(
                        "simplified_net_rate=%.4f is outside [0, 1]; clamping.", rate
                    )
                    rate = max(0.0, min(1.0, rate))
                return rate
            except (TypeError, ValueError):
                logger.warning("Could not parse simplified_net_rate; assuming 0.")
        return 0.0

    def net_pension(self, gross_pension: float, individual_wage: float) -> float:
        return gross_pension * (1.0 - self._flat_rate)

    def effective_rate(self, gross_pension: float, individual_wage: float) -> float:
        return self._flat_rate


# ---------------------------------------------------------------------------
# Progressive bracket engine
# ---------------------------------------------------------------------------

class BracketTaxEngine(TaxEngineBase):
    """Progressive income-tax schedule applied to pension income.

    Parameters
    ----------
    brackets:
        Ordered list of ``(upper_bound, marginal_rate)`` pairs.
        The last bracket's ``upper_bound`` should be ``float("inf")``.
        Example: ``[(20_000, 0.10), (50_000, 0.20), (float("inf"), 0.30)]``
    basic_allowance:
        Annual tax-free allowance.  Pension income below this is untaxed.
    social_contrib_rate:
        Employee social-contribution rate applied on top of income tax.
    average_wage:
        Annual average wage.
    """

    def __init__(
        self,
        brackets: list[tuple[float, float]],
        basic_allowance: float = 0.0,
        social_contrib_rate: float = 0.0,
        average_wage: float = 1.0,
    ) -> None:
        self._brackets = sorted(brackets, key=lambda x: x[0])
        self._allowance = basic_allowance
        self._sc_rate = social_contrib_rate
        self._avg_wage = average_wage

    def _income_tax(self, taxable_income: float) -> float:
        """Compute income tax on taxable income using the bracket schedule."""
        tax = 0.0
        lower = 0.0
        for upper, rate in self._brackets:
            if taxable_income <= lower:
                break
            band = min(taxable_income, upper) - lower
            tax += band * rate
            lower = upper
        return tax

    def net_pension(self, gross_pension: float, individual_wage: float) -> float:
        taxable = max(0.0, gross_pension - self._allowance)
        it = self._income_tax(taxable)
        sc = gross_pension * self._sc_rate
        return gross_pension - it - sc

    def effective_rate(self, gross_pension: float, individual_wage: float) -> float:
        if gross_pension == 0:
            return 0.0
        net = self.net_pension(gross_pension, individual_wage)
        return 1.0 - net / gross_pension


# ---------------------------------------------------------------------------
# Worker-side (accumulation phase) tax engine
# ---------------------------------------------------------------------------

class WorkerTaxEngine:
    """Computes worker-side tax relief on contributions during accumulation.

    Not used in the main OECD-style methodology (contributions are tax-exempt
    under EET), but included for completeness when countries have TEE or TTE
    regimes.
    """

    def __init__(
        self,
        tax_rules: TaxAndContrib,
        average_wage: float,
        bracket_engine: BracketTaxEngine | None = None,
    ) -> None:
        self._rules = tax_rules
        self._avg_wage = average_wage
        self._bracket = bracket_engine

    def tax_treatment_code(self) -> str:
        """Return the EET / TEE / TTE code (or best guess from rules)."""
        t = (self._rules.worker_income_tax_treatment or "").upper()
        if t in {"EET", "TEE", "TTE", "ETT"}:
            return t
        # Default: EET (contributions exempt, fund exempt, benefits taxed)
        return "EET"

    def is_contribution_exempt(self) -> bool:
        return self.tax_treatment_code()[0] == "E"

    def is_benefit_taxed(self) -> bool:
        return self.tax_treatment_code()[-1] == "T"
