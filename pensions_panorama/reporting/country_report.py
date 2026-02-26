"""Country report generator.

Produces a Markdown file (Quarto-compatible) per country that embeds:
  1. Country metadata and pension system overview
  2. Parameter table (schemes, rules, rates)
  3. Results table (6 earnings multiples × all indicators)
  4. Chart image references

The template lives at pensions_panorama/templates/country_report.md.j2
and is rendered with Jinja2, keeping the logic in Python and the
presentation in the template.
"""

from __future__ import annotations

import logging
from pathlib import Path
from datetime import date

import pandas as pd
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from pensions_panorama.config import TEMPLATES_DIR
from pensions_panorama.model.pension_engine import PensionResult
from pensions_panorama.model.assumptions import ModelingAssumptions
from pensions_panorama.schema.params_schema import CountryParams, CoverageStatus
from pensions_panorama.reporting.export import results_to_df

logger = logging.getLogger(__name__)


def _format_pct(v: float) -> str:
    return f"{v * 100:.1f}%"


def _format_x(v: float, decimals: int = 2) -> str:
    return f"{v:.{decimals}f}"


def _build_results_table(results: list[PensionResult]) -> list[dict]:
    """Build a list-of-dicts for template rendering."""
    rows = []
    for r in results:
        rows.append({
            "multiple": f"{r.earnings_multiple:.2f}",
            "gross_pl": _format_pct(r.gross_pension_level),
            "net_pl": _format_pct(r.net_pension_level),
            "gross_rr": _format_pct(r.gross_replacement_rate),
            "net_rr": _format_pct(r.net_replacement_rate),
            "gross_pw": _format_x(r.gross_pension_wealth),
            "net_pw": _format_x(r.net_pension_wealth),
        })
    return rows


def _build_scheme_table(params: CountryParams) -> list[dict]:
    """Summarise schemes as a table for the report."""
    rows = []
    for s in params.schemes:
        e = s.eligibility
        b = s.benefits
        c = s.contributions

        accrual = b.accrual_rate_per_year.value if b.accrual_rate_per_year else "—"
        flat = b.flat_rate_aw_multiple.value if b.flat_rate_aw_multiple else "—"

        contrib_str = "—"
        if c:
            parts = []
            if c.employee_rate and c.employee_rate.value is not None:
                parts.append(f"{float(c.employee_rate.value)*100:.2f}% (ee)")
            if c.employer_rate and c.employer_rate.value is not None:
                parts.append(f"{float(c.employer_rate.value)*100:.2f}% (er)")
            if c.total_rate and c.total_rate.value is not None:
                parts.append(f"{float(c.total_rate.value)*100:.2f}% (total)")
            contrib_str = " + ".join(parts) if parts else "—"

        rows.append({
            "scheme_id": s.scheme_id,
            "name": s.name,
            "type": s.type.value,
            "tier": s.tier.value,
            "coverage": s.coverage,
            "nra_m": e.normal_retirement_age_male.value,
            "nra_f": e.normal_retirement_age_female.value,
            "accrual_or_flat": accrual if accrual != "—" else flat,
            "contributions": contrib_str,
            "indexation": b.indexation or "—",
        })
    return rows


def _build_params_normalized(params: CountryParams, avg_wage: float) -> list[dict]:
    """Key parameters normalised to multiples of average wage."""
    rows = []
    for s in params.schemes:
        b = s.benefits
        c = s.contributions

        def _to_aw(v_opt, aw: float = avg_wage) -> str:
            if v_opt is None:
                return "—"
            v = v_opt.value if hasattr(v_opt, "value") else v_opt
            if v is None:
                return "—"
            try:
                return f"{float(v) / aw:.3f} × AW  ({float(v):,.0f})"
            except (TypeError, ValueError):
                return str(v)

        def _to_pct(sv) -> str:
            if sv is None or sv.value is None:
                return "—"
            return f"{float(sv.value) * 100:.2f}%"

        rows.append({
            "scheme_id": s.scheme_id,
            "parameter": "Accrual rate / flat rate",
            "value_raw": (b.accrual_rate_per_year.value if b.accrual_rate_per_year else
                          (b.flat_rate_aw_multiple.value if b.flat_rate_aw_multiple else "—")),
            "value_aw": (f"{float(b.accrual_rate_per_year.value) * 100:.2f}%/yr"
                         if b.accrual_rate_per_year and b.accrual_rate_per_year.value
                         else _to_pct(b.flat_rate_aw_multiple)),
        })
        if b.minimum_benefit_aw_multiple or b.minimum_benefit_absolute:
            rows.append({
                "scheme_id": s.scheme_id,
                "parameter": "Minimum benefit",
                "value_raw": (b.minimum_benefit_aw_multiple.value
                              if b.minimum_benefit_aw_multiple else
                              (b.minimum_benefit_absolute.value
                               if b.minimum_benefit_absolute else "—")),
                "value_aw": _to_aw(b.minimum_benefit_aw_multiple),
            })
        if c and c.total_rate:
            rows.append({
                "scheme_id": s.scheme_id,
                "parameter": "Total contribution rate",
                "value_raw": c.total_rate.value,
                "value_aw": _to_pct(c.total_rate),
            })
    return rows


def _build_worker_types_context(params: CountryParams) -> dict:
    """Build all worker-type related context for the enhanced report template."""
    wt = params.worker_types
    scheme_ids = {s.scheme_id for s in params.schemes}

    coverage_map = []
    worker_type_details = []
    unknown_worker_types = []
    citations_appendix = []

    # Get resolved private_employee for diff comparison
    private_resolved = None
    if "private_employee" in wt:
        try:
            private_resolved = params.resolve_worker_type("private_employee")
        except Exception:
            pass

    for wt_id, rules in wt.items():
        try:
            resolved = params.resolve_worker_type(wt_id)
        except Exception:
            resolved = rules

        # Coverage map row
        coverage_map.append({
            "wt_id": wt_id,
            "label": resolved.label,
            "coverage_status": resolved.coverage_status.value,
            "scheme_ids": ", ".join(resolved.scheme_ids) if resolved.scheme_ids else "—",
        })

        if resolved.coverage_status == CoverageStatus.UNKNOWN:
            unknown_worker_types.append(wt_id)

        # Eligibility details
        elig_override = resolved.eligibility_override
        elig_rows = []
        if elig_override:
            def _sv_val(sv) -> str:
                return str(sv.value) if sv and sv.value is not None else "—"
            elig_rows = [
                {"param": "NRA (male)", "value": _sv_val(elig_override.normal_retirement_age_male)},
                {"param": "NRA (female)", "value": _sv_val(elig_override.normal_retirement_age_female)},
                {"param": "Early RA (male)", "value": _sv_val(elig_override.early_retirement_age_male)},
                {"param": "Early RA (female)", "value": _sv_val(elig_override.early_retirement_age_female)},
                {"param": "Min contribution years", "value": _sv_val(elig_override.minimum_contribution_years)},
            ]
        else:
            # Pull from first applicable scheme
            applicable = [
                s for s in params.schemes
                if s.scheme_id in (resolved.scheme_ids or []) or not resolved.scheme_ids
            ]
            if applicable:
                e = applicable[0].eligibility
                def _sv_val2(sv) -> str:
                    return str(sv.value) if sv and sv.value is not None else "—"
                elig_rows = [
                    {"param": "NRA (male)", "value": _sv_val2(e.normal_retirement_age_male)},
                    {"param": "NRA (female)", "value": _sv_val2(e.normal_retirement_age_female)},
                    {"param": "Early RA (male)", "value": _sv_val2(e.early_retirement_age_male)},
                    {"param": "Early RA (female)", "value": _sv_val2(e.early_retirement_age_female)},
                    {"param": "Min contribution years", "value": _sv_val2(e.minimum_contribution_years)},
                ]

        # Contribution details
        contrib_rows = []
        co = resolved.contributions_override
        if co:
            def _pct(sv) -> str:
                if sv and sv.value is not None:
                    return f"{float(sv.value) * 100:.2f}%"
                return "—"
            contrib_rows = [
                {"param": "Employee rate", "value": _pct(co.employee_rate)},
                {"param": "Employer rate", "value": _pct(co.employer_rate)},
                {"param": "Total rate", "value": _pct(co.total_rate)},
            ]

        # Diff vs private_employee
        diffs = _diff_worker_type_vs_private(resolved, private_resolved) if private_resolved else []

        # Special provisions
        sp = resolved.special_provisions
        sp_items = []
        if sp:
            for attr in ("lump_sum", "survivor_benefit", "disability_benefit", "partial_pension", "notes"):
                val = getattr(sp, attr)
                if val:
                    sp_items.append({"label": attr.replace("_", " ").title(), "value": val})

        worker_type_details.append({
            "wt_id": wt_id,
            "label": resolved.label,
            "coverage_status": resolved.coverage_status.value,
            "scheme_ids": resolved.scheme_ids,
            "eligibility_rows": elig_rows,
            "contribution_rows": contrib_rows,
            "special_provisions": sp_items,
            "diffs_vs_private": diffs,
            "notes": resolved.notes or "",
            "source_citation": resolved.source_citation,
            "source_url": resolved.source_url or "",
        })

        # Citations appendix entry
        if resolved.source_citation:
            citations_appendix.append({
                "section": f"Worker Types / {wt_id}",
                "parameter": resolved.label,
                "citation": resolved.source_citation,
                "url": resolved.source_url or "",
            })

    return {
        "coverage_map": coverage_map,
        "worker_type_details": worker_type_details,
        "unknown_worker_types": unknown_worker_types,
        "citations_appendix": citations_appendix,
        "has_worker_types": bool(wt),
    }


def _diff_worker_type_vs_private(
    resolved_wt,
    private_wt,
) -> list[str]:
    """Return bullet strings describing how resolved_wt differs from private_wt."""
    diffs = []
    if resolved_wt is None or private_wt is None:
        return diffs

    if resolved_wt.coverage_status != private_wt.coverage_status:
        diffs.append(
            f"Coverage: {resolved_wt.coverage_status.value} "
            f"(vs {private_wt.coverage_status.value} for private employees)"
        )

    wt_schemes = set(resolved_wt.scheme_ids)
    pe_schemes = set(private_wt.scheme_ids)
    if wt_schemes != pe_schemes:
        extra = wt_schemes - pe_schemes
        missing = pe_schemes - wt_schemes
        if extra:
            diffs.append(f"Additional schemes: {', '.join(sorted(extra))}")
        if missing:
            diffs.append(f"Missing schemes: {', '.join(sorted(missing))} (vs private employees)")

    # Eligibility diffs
    wt_elig = resolved_wt.eligibility_override
    pe_elig = private_wt.eligibility_override

    def _sv_val(sv) -> float | None:
        return float(sv.value) if sv and sv.value is not None else None

    if wt_elig or pe_elig:
        wt_nra_m = _sv_val(wt_elig.normal_retirement_age_male) if wt_elig else None
        pe_nra_m = _sv_val(pe_elig.normal_retirement_age_male) if pe_elig else None
        if wt_nra_m is not None and pe_nra_m is not None and wt_nra_m != pe_nra_m:
            diffs.append(f"NRA (male): {wt_nra_m:.0f} (vs {pe_nra_m:.0f} for private employees)")

    # Contribution diffs
    wt_co = resolved_wt.contributions_override
    pe_co = private_wt.contributions_override
    if wt_co or pe_co:
        def _pct(sv) -> str:
            v = _sv_val(sv)
            return f"{v * 100:.2f}%" if v is not None else "—"
        wt_ee = _pct(wt_co.employee_rate if wt_co else None)
        pe_ee = _pct(pe_co.employee_rate if pe_co else None)
        if wt_ee != pe_ee and wt_ee != "—":
            diffs.append(f"Employee contribution: {wt_ee} (vs {pe_ee} for private employees)")

    return diffs


def generate_country_report(
    params: CountryParams,
    results: list[PensionResult],
    assumptions: ModelingAssumptions,
    average_wage: float,
    out_dir: Path,
    chart_paths: dict[str, Path] | None = None,
    macro_df: pd.DataFrame | None = None,
) -> Path:
    """Render a Markdown report for one country.

    Parameters
    ----------
    params:
        Country parameter object.
    results:
        List of PensionResult (one per earnings multiple).
    assumptions:
        Global modeling assumptions used in this run.
    average_wage:
        Annual average wage (national currency) used in calculations.
    out_dir:
        Output directory for this country.
    chart_paths:
        Dict of chart name → absolute Path (embedded as relative in markdown).
    macro_df:
        Optional macro-context DataFrame from World Bank.

    Returns
    -------
    Path to the generated .md file.
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    # Jinja2 environment
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        undefined=StrictUndefined,
        autoescape=False,
    )
    env.filters["pct"] = lambda v: _format_pct(float(v)) if v not in (None, "—") else "—"
    env.filters["xaw"] = lambda v: _format_x(float(v)) if v not in (None, "—") else "—"

    template = env.get_template("country_report.md.j2")

    # Prepare chart relative paths (relative to report directory)
    chart_rel: dict[str, str] = {}
    if chart_paths:
        for name, path in chart_paths.items():
            try:
                rel = path.relative_to(out_dir)
                chart_rel[name] = str(rel)
            except ValueError:
                chart_rel[name] = str(path)

    # Macro context table (last available year per indicator)
    macro_table: list[dict] = []
    if macro_df is not None and not macro_df.empty:
        for col in macro_df.columns:
            if col == "date":
                continue
            valid = macro_df[["date", col]].dropna(subset=[col])
            if not valid.empty:
                row = valid.iloc[-1]
                macro_table.append({
                    "indicator": col,
                    "year": int(row["date"]),
                    "value": f"{row[col]:,.2f}",
                })

    # Worker types context
    worker_types_ctx = _build_worker_types_context(params)

    context = {
        "country_name": params.metadata.country_name,
        "iso3": params.metadata.iso3,
        "currency": params.metadata.currency,
        "currency_code": params.metadata.currency_code,
        "reference_year": params.metadata.reference_year,
        "wb_region": params.metadata.wb_region or "—",
        "sources": params.metadata.sources,
        "last_reviewed": params.metadata.last_reviewed or "—",
        "generated_date": date.today().isoformat(),

        "average_wage": f"{average_wage:,.0f}",
        "average_wage_usd_approx": "—",  # placeholder

        "schemes": _build_scheme_table(params),
        "params_normalized": _build_params_normalized(params, average_wage),
        "results_table": _build_results_table(results),
        "component_headers": list(results[0].component_breakdown.keys()) if results else [],

        "assumptions": {
            "entry_age": assumptions.entry_age,
            "career_length": assumptions.career_length,
            "contribution_density": assumptions.contribution_density,
            "real_wage_growth": f"{assumptions.real_wage_growth * 100:.1f}%",
            "discount_rate": f"{assumptions.discount_rate * 100:.1f}%",
            "indexation_type": assumptions.pension_indexation_type,
            "wpp_year": assumptions.wpp_year,
            "sex": assumptions.sex,
        },
        "tax_notes": params.taxes.notes or "—",
        "pension_notes": params.notes or "—",

        "charts": chart_rel,
        "macro_table": macro_table,

        # Worker types (new)
        "coverage_map": worker_types_ctx["coverage_map"],
        "worker_type_details": worker_types_ctx["worker_type_details"],
        "unknown_worker_types": worker_types_ctx["unknown_worker_types"],
        "citations_appendix": worker_types_ctx["citations_appendix"],
        "has_worker_types": worker_types_ctx["has_worker_types"],
    }

    content = template.render(**context)
    out_path = out_dir / f"{params.metadata.iso3}_report.md"
    out_path.write_text(content, encoding="utf-8")
    logger.info("Generated country report: %s", out_path)
    return out_path


def generate_panorama_summary(
    country_results: dict[str, tuple[CountryParams, list[PensionResult]]],
    out_dir: Path,
    ref_earnings_multiple: float = 1.0,
) -> Path:
    """Generate a cross-country summary Markdown report.

    Parameters
    ----------
    country_results:
        Mapping iso3 → (CountryParams, list[PensionResult]).
    out_dir:
        Output directory for the panorama summary.
    ref_earnings_multiple:
        The earnings multiple to highlight in the summary table.
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for iso3, (params, results) in country_results.items():
        ref_result = next(
            (r for r in results if abs(r.earnings_multiple - ref_earnings_multiple) < 0.01),
            results[0] if results else None,
        )
        if ref_result is None:
            continue
        rows.append({
            "Country": params.metadata.country_name,
            "ISO3": iso3,
            "NRA (M)": params.schemes[0].eligibility.normal_retirement_age_male.value
            if params.schemes
            else "—",
            "NRA (F)": params.schemes[0].eligibility.normal_retirement_age_female.value
            if params.schemes
            else "—",
            f"Gross RR @ {ref_earnings_multiple}×AW": _format_pct(ref_result.gross_replacement_rate),
            f"Net RR @ {ref_earnings_multiple}×AW": _format_pct(ref_result.net_replacement_rate),
            f"Gross PW @ {ref_earnings_multiple}×AW": _format_x(ref_result.gross_pension_wealth),
        })

    df = pd.DataFrame(rows)

    lines = [
        "# Pensions Panorama – Summary Report",
        "",
        f"_Generated: {date.today().isoformat()}_",
        "",
        "## Countries Covered",
        "",
        df.to_markdown(index=False) if not df.empty else "_No data available._",
        "",
        "---",
        "",
        "## Notes",
        "",
        "- All figures computed at the specified earnings multiples relative to "
        "national average wage.",
        "- Gross replacement rate = gross annual pension ÷ individual pre-retirement wage.",
        "- Pension wealth = present value of benefit stream ÷ average wage, "
        "survival-weighted where UN life-table data are available.",
        "- Figures reflect the main mandatory scheme(s) only. Supplementary or "
        "voluntary tiers may not be included.",
    ]

    content = "\n".join(lines)
    out_path = out_dir / "panorama_summary.md"
    out_path.write_text(content, encoding="utf-8")
    logger.info("Generated panorama summary: %s", out_path)
    return out_path
