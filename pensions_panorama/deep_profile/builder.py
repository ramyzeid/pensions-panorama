"""Build deep profile JSON outputs."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import json
import yaml

from pensions_panorama.config import DEEP_PROFILE_DIR, RunConfig
from pensions_panorama.schema.deep_profile_schema import (
    CellValue,
    DeepProfile,
    IndicatorItem,
    NarrativeBlock,
    SchemeItem,
    SchemeTypeGroup,
    SourceRef,
)
from pensions_panorama.sources.worldbank import WorldBankClient
from pensions_panorama.schema.params_schema import CountryParams, SchemeComponent


DEEP_PROFILE_MAPPING_DIR = Path(__file__).parent.parent.parent / "data" / "deep_profiles"

WDI_INDICATORS = {
    "gdp_pc_lcu": {
        "label": "GDP per capita (LCU)",
        "indicator_id": "NY.GDP.PCAP.CN",
        "unit": "LCU",
    },
    "gdp_pc_usd": {
        "label": "GDP per capita (USD)",
        "indicator_id": "NY.GDP.PCAP.CD",
        "unit": "USD",
    },
    "pop_65_total": {
        "label": "Population age 65+ (total)",
        "indicator_id": "SP.POP.65UP.TO",
        "unit": "persons",
    },
    "pop_65_pct": {
        "label": "Population age 65+ (% of total population)",
        "indicator_id": "SP.POP.65UP.TO.ZS",
        "unit": "%",
    },
    # ASPIRE – Atlas of Social Protection Indicators (World Bank)
    # Coverage data comes from household surveys; sparse for high-income countries.
    "pension_coverage_pct": {
        "label": "Contributory pension coverage (% of population)",
        "indicator_id": "per_si_cp.cov_pop_tot",
        "unit": "%",
        "source_name": "ASPIRE – World Bank",
        "source_url": "https://www.worldbank.org/en/data/datatopics/aspire",
    },
    "social_insurance_coverage_pct": {
        "label": "Social insurance coverage (% of population)",
        "indicator_id": "per_si_allsi.cov_pop_tot",
        "unit": "%",
        "source_name": "ASPIRE – World Bank",
        "source_url": "https://www.worldbank.org/en/data/datatopics/aspire",
    },
    # GFDD – Global Financial Development Database (World Bank / OECD GPS)
    # Pension fund assets as % of GDP; strongest for funded DC systems.
    "pension_fund_assets_gdp": {
        "label": "Pension fund assets (% of GDP)",
        "indicator_id": "GFDD.DI.13",
        "unit": "%",
        "source_name": "Global Financial Development Database – World Bank",
        "source_url": "https://data.worldbank.org/indicator/GFDD.DI.13",
    },
}

SYSTEM_KPI_DEFAULTS = [
    {
        "key": "coverage_total",
        "label": "Social insurance coverage (% of population)",
        "default_indicator_id": "per_si_allsi.cov_pop_tot",
        "default_unit": "%",
        "default_source_name": "ASPIRE – World Bank",
        "default_source_url": "https://www.worldbank.org/en/data/datatopics/aspire",
    },
    {
        "key": "pension_coverage",
        "label": "Contributory pension coverage (% of population)",
        "default_indicator_id": "per_si_cp.cov_pop_tot",
        "default_unit": "%",
        "default_source_name": "ASPIRE – World Bank",
        "default_source_url": "https://www.worldbank.org/en/data/datatopics/aspire",
    },
    {
        "key": "pension_fund_assets_gdp",
        "label": "Pension fund assets (% of GDP)",
        "default_indicator_id": "GFDD.DI.13",
        "default_unit": "%",
        "default_source_name": "Global Financial Development Database – World Bank",
        "default_source_url": "https://data.worldbank.org/indicator/GFDD.DI.13",
    },
    {
        "key": "coverage_65plus",
        "label": "Pension coverage – population age 65+ (%)",
        "default_indicator_id": None,
        "default_unit": "%",
        "default_source_name": None,
    },
    {
        "key": "pension_spending_gdp",
        "label": "Pension expenditure (% of GDP)",
        "default_indicator_id": None,
        "default_unit": "%",
        "default_source_name": None,
    },
]

SCHEME_ATTR_ORDER = [
    ("implementing_agency", "Implementing Agency"),
    ("target_population", "Target Population"),
    ("benefit_plan_type", "Benefit Plan Type"),
    ("financing_mechanism", "Financing Mechanism"),
    ("contrib_employee", "Contribution Rate (Employee)"),
    ("contrib_employer", "Contribution Rate (Employer)"),
    ("contrib_total", "Contribution Rate (Total)"),
    ("ret_age_male", "Retirement Age (Male)"),
    ("ret_age_female", "Retirement Age (Female)"),
    ("members_total", "Members, Total"),
    ("members_pct_adult", "Members (% of adult population)"),
    ("contributors_total", "Annual Contributors, Total"),
    ("contributors_pct_lf", "Contributors (% of labor force)"),
    ("beneficiaries_total", "Annual Beneficiaries, Total"),
    ("beneficiaries_pct_lf", "Beneficiaries (% of labor force)"),
    ("beneficiaries_pct_total", "Beneficiaries (% of total population)"),
    ("beneficiaries_pct_65plus", "Beneficiaries (% of population 65+)"),
    ("rev_contrib_gdp", "Revenues from contributions (% of GDP)"),
    ("rev_govt_gdp", "Revenues from government transfers (% of GDP)"),
    ("rev_other_gdp", "Other revenues (% of GDP)"),
    ("expenditure_total_gdp", "Annual total program expenditure (% of GDP)"),
    ("benefit_payments_gdp", "Annual benefit payments, total (% of GDP)"),
    ("benefit_payments_lcu", "Annual benefit payments in LCU, total"),
]


def _load_mapping(iso3: str) -> dict[str, Any]:
    path = DEEP_PROFILE_MAPPING_DIR / f"{iso3.upper()}.yaml"
    if not path.exists():
        return {}
    with open(path) as fh:
        return yaml.safe_load(fh) or {}


def _cell_from_mapping(raw: dict[str, Any] | None) -> CellValue:
    if not raw:
        return CellValue()
    source = None
    if raw.get("source_name") or raw.get("source_url"):
        source = SourceRef(
            source_name=raw.get("source_name"),
            source_url=raw.get("source_url"),
            indicator_id=raw.get("indicator_id"),
            year=raw.get("year"),
            notes=raw.get("notes"),
        )
    return CellValue(
        value=raw.get("value"),
        unit=raw.get("unit"),
        year=raw.get("year"),
        source=source,
        notes=raw.get("notes"),
    )


def _latest_value_and_year(wb: WorldBankClient, iso3: str, indicator: str,
                           start_year: int, end_year: int) -> tuple[float | None, int | None]:
    df = wb.fetch_indicator(iso3, indicator, start_year, end_year)
    if df.empty:
        return None, None
    valid = df.dropna(subset=["value"])
    if valid.empty:
        return None, None
    row = valid.iloc[-1]
    value = float(row["value"]) if row["value"] is not None else None
    year = int(row["date"]) if row.get("date") is not None else None
    return value, year


def _build_country_indicators(
    iso3: str,
    wb: WorldBankClient,
    cfg: RunConfig,
    mapping: dict[str, Any],
    offline: bool,
) -> list[IndicatorItem]:
    values: dict[str, tuple[float | None, int | None]] = {}
    years: list[int] = []
    overrides = {
        item.get("key"): item for item in (mapping.get("country_indicators") or []) if item.get("key")
    }

    for key, meta in WDI_INDICATORS.items():
        if offline:
            val, yr = None, None
        else:
            val, yr = _latest_value_and_year(wb, iso3, meta["indicator_id"],
                                             cfg.start_year, cfg.end_year)
        values[key] = (val, yr)
        if yr is not None:
            years.append(yr)

    latest_year = max(years) if years else None
    indicators: list[IndicatorItem] = []

    year_override = overrides.get("year")
    if year_override:
        year_cell = _cell_from_mapping(year_override)
    else:
        year_cell = CellValue(
            value=latest_year,
            unit="year",
            year=latest_year,
            source=SourceRef(
                source_name="World Development Indicators (World Bank)",
                source_url="https://data.worldbank.org",
            ),
        )
    indicators.append(IndicatorItem(key="year", label="Year", cell=year_cell))

    for key, meta in WDI_INDICATORS.items():
        override = overrides.get(key)
        if override:
            cell = _cell_from_mapping(override)
        else:
            val, yr = values[key]
            src_name = meta.get("source_name", "World Development Indicators (World Bank)")
            src_url = meta.get(
                "source_url",
                f"https://data.worldbank.org/indicator/{meta['indicator_id']}?locations={iso3}",
            )
            cell = CellValue(
                value=val,
                unit=meta["unit"],
                year=yr,
                source=SourceRef(
                    source_name=src_name,
                    source_url=src_url,
                    indicator_id=meta["indicator_id"],
                    year=yr,
                ),
            )
        indicators.append(IndicatorItem(key=key, label=meta["label"], cell=cell))

    return indicators


def _build_system_kpis(
    mapping: dict[str, Any],
    iso3: str,
    wb: WorldBankClient,
    cfg: RunConfig,
    offline: bool,
) -> list[IndicatorItem]:
    items = []
    mapping_kpis = {k.get("key"): k for k in mapping.get("system_kpis", []) if k.get("key")}
    for kpi in SYSTEM_KPI_DEFAULTS:
        key = kpi["key"]
        raw = mapping_kpis.get(key) or {}
        cell = _cell_from_mapping(raw) if raw else CellValue()

        # 1. Auto-fill from indicator_id specified in the mapping YAML
        if cell.value is None and raw.get("indicator_id") and not offline:
            ind = raw["indicator_id"]
            val, yr = _latest_value_and_year(wb, iso3, ind, cfg.start_year, cfg.end_year)
            cell.value = val
            cell.year = yr
            if cell.unit is None and raw.get("unit"):
                cell.unit = raw["unit"]
            if cell.source is None:
                cell.source = SourceRef(
                    source_name=raw.get("source_name") or "World Development Indicators (World Bank)",
                    source_url=raw.get("source_url")
                    or f"https://data.worldbank.org/indicator/{ind}?locations={iso3}",
                    indicator_id=ind,
                    year=yr,
                )

        # 2. Fall back to hardcoded default indicator (ASPIRE / GFDD)
        default_ind = kpi.get("default_indicator_id")
        if cell.value is None and default_ind and not offline:
            val, yr = _latest_value_and_year(wb, iso3, default_ind, cfg.start_year, cfg.end_year)
            cell.value = val
            cell.year = yr
            cell.unit = cell.unit or kpi.get("default_unit")
            cell.source = SourceRef(
                source_name=kpi.get("default_source_name") or "World Bank",
                source_url=kpi.get("default_source_url")
                or f"https://data.worldbank.org/indicator/{default_ind}?locations={iso3}",
                indicator_id=default_ind,
                year=yr,
            )

        items.append(IndicatorItem(key=key, label=kpi["label"], cell=cell))
    return items


def _build_schemes(mapping: dict[str, Any], params: CountryParams | None = None) -> list[SchemeItem]:
    schemes = []
    mapping_schemes = mapping.get("schemes") or []

    if mapping_schemes:
        # Use explicit mapping
        for s in mapping_schemes:
            scheme_id = s.get("scheme_id") or s.get("schemeId")
            scheme_name = s.get("scheme_name") or s.get("schemeName") or scheme_id
            scheme_type = s.get("scheme_type_group") or s.get("schemeTypeGroup") or "db"
            attrs_raw = s.get("attributes") or {}
            attrs: dict[str, CellValue] = {}
            for key, _label in SCHEME_ATTR_ORDER:
                attrs[key] = _cell_from_mapping(attrs_raw.get(key))
            schemes.append(SchemeItem(
                scheme_id=scheme_id,
                scheme_name=scheme_name,
                scheme_type_group=SchemeTypeGroup(scheme_type),
                attributes=attrs,
            ))
    elif params is not None:
        # Auto-generate from params YAML
        for s in params.schemes:
            schemes.append(_auto_scheme_from_params(s))

    def _order_key(item: SchemeItem) -> tuple[int, str]:
        order = {"noncontrib": 0, "dc": 1, "db": 2}
        return (order.get(item.scheme_type_group.value, 9), item.scheme_name)

    return sorted(schemes, key=_order_key)


_SCHEME_TYPE_TO_GROUP: dict[str, str] = {
    "DB": "db",
    "NDC": "db",
    "DC": "dc",
    "points": "db",
    "basic": "noncontrib",
}

_SCHEME_TYPE_TO_FINANCING: dict[str, str] = {
    "DB": "Pay As You Go (PAYG)",
    "NDC": "Notional Defined Contribution (NDC)",
    "DC": "Fully funded",
    "points": "Pay As You Go (PAYG) – points system",
    "basic": "General revenue / Social assistance",
}


def _auto_scheme_from_params(s: SchemeComponent) -> SchemeItem:
    """Auto-generate a SchemeItem from a params SchemeComponent using available fields."""
    type_val = s.type.value if hasattr(s.type, "value") else str(s.type)
    type_group = _SCHEME_TYPE_TO_GROUP.get(type_val, "db")
    financing = _SCHEME_TYPE_TO_FINANCING.get(type_val, "")
    ilo_src = "ILO Social Security Inquiry / country YAML parameters"

    attrs: dict[str, CellValue] = {}

    attrs["implementing_agency"] = CellValue(value=s.name)
    if s.coverage:
        attrs["target_population"] = CellValue(value=s.coverage)
    attrs["benefit_plan_type"] = CellValue(value=type_val)
    if financing:
        attrs["financing_mechanism"] = CellValue(value=financing)

    # Contribution rates (stored as decimals → convert to %)
    contrib = s.contributions  # may be None for non-contributory schemes
    emp = contrib.employee_rate.value if (contrib and contrib.employee_rate) else None
    er = contrib.employer_rate.value if (contrib and contrib.employer_rate) else None
    emp_src = (
        contrib.employee_rate.source_citation
        if (contrib and contrib.employee_rate) else None
    ) or ilo_src

    if emp is not None:
        attrs["contrib_employee"] = CellValue(
            value=round(emp * 100, 3),
            unit="%",
            source=SourceRef(source_name=emp_src),
        )
    if er is not None:
        attrs["contrib_employer"] = CellValue(
            value=round(er * 100, 3),
            unit="%",
            source=SourceRef(source_name=emp_src),
        )
    if emp is not None and er is not None:
        attrs["contrib_total"] = CellValue(
            value=round((emp + er) * 100, 3),
            unit="%",
            notes="Derived: employee + employer",
        )
    elif (contrib and contrib.total_rate and contrib.total_rate.value is not None):
        attrs["contrib_total"] = CellValue(
            value=round(s.contributions.total_rate.value * 100, 3),
            unit="%",
        )

    # Retirement ages
    nra_m = s.eligibility.normal_retirement_age_male.value if s.eligibility.normal_retirement_age_male else None
    nra_f = s.eligibility.normal_retirement_age_female.value if s.eligibility.normal_retirement_age_female else None
    nra_src = (
        s.eligibility.normal_retirement_age_male.source_citation
        if s.eligibility.normal_retirement_age_male else None
    ) or ilo_src
    if nra_m is not None:
        attrs["ret_age_male"] = CellValue(value=nra_m, source=SourceRef(source_name=nra_src))
    if nra_f is not None:
        attrs["ret_age_female"] = CellValue(value=nra_f, source=SourceRef(source_name=nra_src))

    return SchemeItem(
        scheme_id=s.scheme_id if hasattr(s, "scheme_id") else s.name,
        scheme_name=s.name,
        scheme_type_group=SchemeTypeGroup(type_group),
        attributes=attrs,
    )


def _build_narrative(mapping: dict[str, Any], params: CountryParams | None) -> NarrativeBlock:
    if mapping.get("narrative"):
        raw = mapping["narrative"]
        sources = [SourceRef(**s) for s in raw.get("sources", [])]
        return NarrativeBlock(text=raw.get("text", ""), sources=sources)

    if params is None:
        return NarrativeBlock(text="Not available.", sources=[])

    # Richer fallback narrative using available structured fields
    m = params.metadata
    schemes = params.schemes
    main_scheme = schemes[0]
    nra_m = main_scheme.eligibility.normal_retirement_age_male.value if main_scheme.eligibility.normal_retirement_age_male else None
    nra_f = main_scheme.eligibility.normal_retirement_age_female.value if main_scheme.eligibility.normal_retirement_age_female else None
    _contrib = main_scheme.contributions
    emp = (_contrib.employee_rate.value if _contrib and _contrib.employee_rate else None)
    er = (_contrib.employer_rate.value if _contrib and _contrib.employer_rate else None)
    type_val = main_scheme.type.value if hasattr(main_scheme.type, "value") else str(main_scheme.type)

    contrib_str = ""
    if emp is not None and er is not None:
        contrib_str = (
            f" Contributions total {(emp + er) * 100:.1f}% of insurable earnings "
            f"({emp * 100:.1f}% employee, {er * 100:.1f}% employer)."
        )
    elif emp is not None:
        contrib_str = f" Employee contribution rate is {emp * 100:.1f}%."

    region_label = {
        "SSA": "Sub-Saharan Africa",
        "EAP": "East Asia and Pacific",
        "SAS": "South Asia",
        "ECS": "Europe and Central Asia",
        "LCN": "Latin America and the Caribbean",
        "MEA": "Middle East and North Africa",
        "NAC": "North America",
    }.get(m.wb_region or "", m.wb_region or "")

    if nra_m is not None and nra_f is not None:
        nra_str = f"The normal retirement age is {nra_m}" + (
            f" for men and {nra_f} for women." if nra_f != nra_m else " for both men and women."
        )
    elif nra_m is not None:
        nra_str = f"The normal retirement age is {nra_m}."
    else:
        nra_str = ""

    scheme_list = ", ".join(s.name for s in schemes)
    multi_str = (
        f" The system includes {len(schemes)} schemes: {scheme_list}."
        if len(schemes) > 1
        else ""
    )

    text = (
        f"{m.country_name} is a {region_label} country with a "
        f"{type_val}-type pension system centred on the {main_scheme.name}."
        f"{multi_str} {nra_str}{contrib_str}"
    )

    sources = []
    if m.sources:
        for s_name in m.sources[:2]:
            sources.append(SourceRef(source_name=s_name))
    return NarrativeBlock(text=text, sources=sources)


def build_deep_profile(
    iso3: str,
    params: CountryParams | None,
    cfg: RunConfig,
    wb_client: WorldBankClient,
    offline: bool = False,
) -> DeepProfile:
    mapping = _load_mapping(iso3)
    country_name = (params.metadata.country_name if params else mapping.get("country_name")) or iso3

    narrative = _build_narrative(mapping, params)
    country_indicators = _build_country_indicators(iso3, wb_client, cfg, mapping, offline)
    system_kpis = _build_system_kpis(mapping, iso3, wb_client, cfg, offline)
    schemes = _build_schemes(mapping, params)

    return DeepProfile(
        iso3=iso3,
        country_name=country_name,
        last_updated=datetime.now(timezone.utc),
        narrative=narrative,
        country_indicators=country_indicators,
        system_kpis=system_kpis,
        schemes=schemes,
    )


def write_deep_profile(profile: DeepProfile, out_dir: Path | None = None) -> Path:
    out_dir = out_dir or DEEP_PROFILE_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{profile.iso3}.json"
    path.write_text(json.dumps(profile.model_dump_jsonable(), ensure_ascii=True, indent=2))
    return path
