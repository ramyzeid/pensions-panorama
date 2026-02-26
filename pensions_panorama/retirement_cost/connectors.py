"""Sync HTTP connectors for retirement cost data (WDI, WHO GHO, UN WPP).

Uses requests + simple in-process caching (st.cache_data wraps these at call site).
"""
from __future__ import annotations

import logging
from typing import Optional

import requests

logger = logging.getLogger(__name__)

_SESSION = requests.Session()
_SESSION.headers.update({"User-Agent": "pensions-panorama/1.0"})
_TIMEOUT = 20


# ---------------------------------------------------------------------------
# WDI
# ---------------------------------------------------------------------------
WDI_CODES = {
    "hfce_pc_2015usd": "NE.CON.PRVT.PC.KD",
    "che_pc_usd": "SH.XPD.CHEX.PC.CD",
    "oop_pct_che": "SH.XPD.OOPC.CH.ZS",
    "ppp_factor": "PA.NUS.PPP",
    "gdp_pc_usd": "NY.GDP.PCAP.CD",
}


def _wdi_fetch(iso3: str, code: str, mrv: int = 10) -> Optional[tuple[float, int]]:
    """Return (value, year) for most recent non-null WDI observation."""
    url = f"https://api.worldbank.org/v2/country/{iso3}/indicator/{code}"
    params = {"format": "json", "mrv": mrv, "per_page": 20}
    try:
        r = _SESSION.get(url, params=params, timeout=_TIMEOUT)
        r.raise_for_status()
        raw = r.json()
        if not isinstance(raw, list) or len(raw) < 2 or not raw[1]:
            return None
        for item in raw[1]:
            if item.get("value") is not None:
                return float(item["value"]), int(item["date"])
    except Exception as e:
        logger.warning("WDI fetch failed for %s/%s: %s", iso3, code, e)
    return None


def fetch_wdi_inputs(iso3: str) -> dict[str, Optional[tuple[float, int]]]:
    """Fetch all WDI indicators needed for retirement cost calculation."""
    return {key: _wdi_fetch(iso3, code) for key, code in WDI_CODES.items()}


# ---------------------------------------------------------------------------
# WHO GHO — HALE at 60
# ---------------------------------------------------------------------------
def fetch_hale_at_60(iso3: str) -> Optional[tuple[float, int]]:
    """Return (hale_at_60_total, year) from WHO GHO."""
    code = "WHOSIS_000007"
    url = f"https://ghoapi.azureedge.net/api/{code}"
    params = {
        "$filter": f"SpatialDim eq '{iso3}' and TimeDim ge 2010",
        "$select": "SpatialDim,TimeDim,Dim1,NumericValue",
    }
    try:
        r = _SESSION.get(url, params=params, timeout=_TIMEOUT)
        r.raise_for_status()
        items = r.json().get("value", [])
        total_items = [
            (int(i["TimeDim"]), float(i["NumericValue"]))
            for i in items
            if i.get("Dim1") == "SEX_BTSX" and i.get("NumericValue") is not None
        ]
        if total_items:
            year, val = max(total_items, key=lambda x: x[0])
            return val, year
    except Exception as e:
        logger.warning("WHO GHO HALE fetch failed for %s: %s", iso3, e)
    return None


# ---------------------------------------------------------------------------
# UN WPP — age-specific life expectancy
# ---------------------------------------------------------------------------
ISO3_TO_UN_LOC: dict[str, int] = {
    "SAU": 682, "ARE": 784, "EGY": 818, "JOR": 400,
    "MAR": 504, "PAK": 586, "IND": 356, "BGD": 50,
    "LBN": 422, "TUN": 788, "BHR": 48, "DZA": 12,
    "KWT": 414, "OMN": 512, "QAT": 634, "IRN": 364,
    "TUR": 792, "LKA": 144, "IRQ": 368, "LBY": 434,
    "MRT": 478, "DJI": 262, "NPL": 524, "SDN": 729,
    "SYR": 760, "YEM": 887, "PSE": 275, "MDV": 462,
}


def fetch_le_at_age(iso3: str, retirement_age: int, sex: str = "total") -> Optional[tuple[float, int]]:
    """Fetch remaining life expectancy at exact retirement age from UN WPP."""
    loc = ISO3_TO_UN_LOC.get(iso3)
    if loc is None:
        return None

    sex_id = {"male": 1, "female": 2, "total": 3}.get(sex, 3)
    url = f"https://population.un.org/dataportalapi/api/v1/data/indicators/75/locations/{loc}/start/2020/end/2030"
    params = {"sexId": sex_id, "pageSize": 200}
    try:
        r = _SESSION.get(url, params=params, timeout=_TIMEOUT)
        r.raise_for_status()
        items = r.json().get("data", [])
        matches = [
            (int(str(i.get("timeLabel", "0")).split("-")[0]), float(i["value"]))
            for i in items
            if str(i.get("ageLabel", "")).strip() == str(retirement_age)
            and i.get("value") is not None
        ]
        if matches:
            year, val = max(matches, key=lambda x: x[0])
            return val, year
    except Exception as e:
        logger.warning("UN WPP LE fetch failed for %s age %d: %s", iso3, retirement_age, e)
    return None


# ---------------------------------------------------------------------------
# High-level assembly
# ---------------------------------------------------------------------------
def build_retirement_inputs_sync(
    iso3: str,
    retirement_age: int,
    sex: str,
    scenario: str,
    discount_rate: float,
    inflation_rate: float,
    age_uplift_factor: float,
    include_health_oop: bool,
    use_hale_split: bool,
) -> "RetirementInputs":  # noqa: F821
    """Fetch all data and return a RetirementInputs ready for run_calculation()."""
    from .types import RetirementInputs

    sources: list[dict] = []
    data_quality: dict = {}

    # 1. Retirement horizon (UN WPP → WHO GHO fallback)
    le_result = fetch_le_at_age(iso3, retirement_age, sex)
    if le_result:
        remaining_le, le_year = le_result
        horizon_method = "UN_WPP_exact"
        sources.append({
            "source": "UN WPP", "code": f"LE_AT_{retirement_age}",
            "year": le_year, "url": "https://population.un.org/wpp/",
            "proxy_used": False,
        })
        data_quality["life_expectancy"] = {"status": "ok", "year": le_year, "method": "UN_WPP"}
    else:
        hale_result = fetch_hale_at_60(iso3)
        if hale_result:
            remaining_le, le_year = hale_result
            horizon_method = "WHO_GHO_LE60_proxy"
            sources.append({
                "source": "WHO GHO", "code": "WHOSIS_000007",
                "year": le_year,
                "url": "https://www.who.int/data/gho/data/indicators/indicator-details/GHO/WHOSIS_000007",
                "proxy_used": True,
            })
            data_quality["life_expectancy"] = {"status": "proxy", "year": le_year, "method": "WHO_GHO_LE60"}
        else:
            remaining_le = None
            horizon_method = "insufficient"
            data_quality["life_expectancy"] = {"status": "missing"}

    # 2. HALE at retirement (WHO GHO)
    hale_result2 = fetch_hale_at_60(iso3)
    hale_at_retirement: Optional[float] = None
    if hale_result2:
        hale_val, hale_year = hale_result2
        hale_at_retirement = hale_val * (60.0 / retirement_age) if retirement_age > 60 else hale_val
        if not any(s["code"] == "WHOSIS_000007" for s in sources):
            sources.append({
                "source": "WHO GHO", "code": "WHOSIS_000007",
                "year": hale_year,
                "url": "https://www.who.int/data/gho/data/indicators/indicator-details/GHO/WHOSIS_000007",
                "proxy_used": retirement_age > 60,
            })
        data_quality["hale"] = {"status": "ok", "year": hale_year}
    else:
        data_quality["hale"] = {"status": "missing"}

    # 3. WDI indicators
    wdi = fetch_wdi_inputs(iso3)

    def _v(key: str) -> Optional[float]:
        return wdi[key][0] if wdi.get(key) else None

    def _y(key: str) -> Optional[int]:
        return wdi[key][1] if wdi.get(key) else None

    ppp_factor = _v("ppp_factor")
    hfce_2015usd = _v("hfce_pc_2015usd")
    hfce_pc_lc = (hfce_2015usd * ppp_factor) if hfce_2015usd and ppp_factor else None

    for key, code in WDI_CODES.items():
        if wdi.get(key):
            year = _y(key)
            sources.append({
                "source": "World Bank WDI", "code": code,
                "year": year,
                "url": f"https://data.worldbank.org/indicator/{code}?locations={iso3}",
                "proxy_used": False,
            })
            data_quality[key] = {"status": "ok", "year": year}
        else:
            data_quality[key] = {"status": "missing"}

    return RetirementInputs(
        country_iso3=iso3,
        retirement_age=retirement_age,
        sex=sex,
        scenario=scenario,
        remaining_le_years=remaining_le,
        hale_at_retirement=hale_at_retirement,
        horizon_method=horizon_method,
        hfce_pc_lc=hfce_pc_lc,
        che_pc_usd=_v("che_pc_usd"),
        oop_pct_che=_v("oop_pct_che"),
        ppp_factor=ppp_factor,
        gdp_pc_usd=_v("gdp_pc_usd"),
        national_poverty_line_annual_lc=None,
        discount_rate=discount_rate,
        inflation_rate=inflation_rate,
        age_uplift_factor=age_uplift_factor,
        include_health_oop=include_health_oop,
        use_hale_split=use_hale_split,
        sources=sources,
        data_quality=data_quality,
    )
