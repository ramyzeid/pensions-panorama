"""Export utilities: CSV and Excel workbooks.

Functions
---------
results_to_df(results, iso3, country_name) → pd.DataFrame
    Convert a list of PensionResult objects to a tidy DataFrame.

export_country_csv(results, iso3, country_name, out_dir) → Path

export_country_excel(results, iso3, country_name, params, out_dir) → Path
    Writes an Excel file with:
      - Sheet "results"   : the main indicators table
      - Sheet "params"    : flattened country parameters (for transparency)
      - Sheet "breakdown" : component-level gross pension breakdown

export_panorama_excel(all_country_dfs, out_dir) → Path
    Writes a combined Excel workbook with one sheet per country plus a
    "Comparative" sheet with key indicators side-by-side.

export_panorama_csv(all_country_dfs, out_dir) → Path
    Writes a single merged CSV with all countries stacked.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from pensions_panorama.model.pension_engine import PensionResult
from pensions_panorama.schema.params_schema import CountryParams

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Column labels for the results table
# ---------------------------------------------------------------------------
_RESULT_COLUMNS = {
    "earnings_multiple": "Earnings multiple (×AW)",
    "individual_wage": "Individual wage (currency)",
    "gross_benefit": "Gross pension (currency)",
    "net_benefit": "Net pension (currency)",
    "gross_replacement_rate": "Gross replacement rate",
    "net_replacement_rate": "Net replacement rate",
    "gross_pension_level": "Gross pension level (% AW)",
    "net_pension_level": "Net pension level (% AW)",
    "gross_pension_wealth": "Gross pension wealth (×AW)",
    "net_pension_wealth": "Net pension wealth (×AW)",
}


# ---------------------------------------------------------------------------
# Conversion helpers
# ---------------------------------------------------------------------------

def results_to_df(
    results: list[PensionResult],
    iso3: str,
    country_name: str,
) -> pd.DataFrame:
    """Convert a list of PensionResult objects to a tidy DataFrame."""
    rows = []
    for r in results:
        row: dict = {
            "iso3": iso3,
            "country_name": country_name,
            "earnings_multiple": r.earnings_multiple,
            "individual_wage": round(r.individual_wage, 2),
            "average_wage": round(r.average_wage, 2),
            "gross_benefit": round(r.gross_benefit, 2),
            "net_benefit": round(r.net_benefit, 2),
            "gross_replacement_rate": round(r.gross_replacement_rate, 6),
            "net_replacement_rate": round(r.net_replacement_rate, 6),
            "gross_pension_level": round(r.gross_pension_level, 6),
            "net_pension_level": round(r.net_pension_level, 6),
            "gross_pension_wealth": round(r.gross_pension_wealth, 4),
            "net_pension_wealth": round(r.net_pension_wealth, 4),
        }
        # Add component breakdown columns
        for scheme_id, val in r.component_breakdown.items():
            row[f"comp_{scheme_id}"] = round(val, 2)
        rows.append(row)
    return pd.DataFrame(rows)


def _params_to_df(params: CountryParams) -> pd.DataFrame:
    """Flatten country parameters to a two-column (parameter, value) DataFrame."""
    rows = []

    def _add(section: str, key: str, value: object, citation: str = "") -> None:
        rows.append({"section": section, "parameter": key, "value": str(value),
                     "source_citation": citation})

    m = params.metadata
    _add("metadata", "country_name", m.country_name)
    _add("metadata", "iso3", m.iso3)
    _add("metadata", "currency", m.currency)
    _add("metadata", "reference_year", m.reference_year)
    _add("metadata", "wb_region", m.wb_region or "")

    for scheme in params.schemes:
        sec = f"scheme:{scheme.scheme_id}"
        _add(sec, "name", scheme.name)
        _add(sec, "type", scheme.type.value)
        _add(sec, "tier", scheme.tier.value)
        _add(sec, "coverage", scheme.coverage)

        e = scheme.eligibility
        _add(sec, "nra_male", e.normal_retirement_age_male.value,
             e.normal_retirement_age_male.source_citation)
        _add(sec, "nra_female", e.normal_retirement_age_female.value,
             e.normal_retirement_age_female.source_citation)
        if e.vesting_years:
            _add(sec, "vesting_years", e.vesting_years.value, e.vesting_years.source_citation)

        b = scheme.benefits
        if b.accrual_rate_per_year:
            _add(sec, "accrual_rate_per_year", b.accrual_rate_per_year.value,
                 b.accrual_rate_per_year.source_citation)
        if b.flat_rate_aw_multiple:
            _add(sec, "flat_rate_aw_multiple", b.flat_rate_aw_multiple.value,
                 b.flat_rate_aw_multiple.source_citation)
        if b.minimum_benefit_aw_multiple:
            _add(sec, "minimum_benefit_aw_multiple", b.minimum_benefit_aw_multiple.value,
                 b.minimum_benefit_aw_multiple.source_citation)
        if b.maximum_benefit_aw_multiple:
            _add(sec, "maximum_benefit_aw_multiple", b.maximum_benefit_aw_multiple.value,
                 b.maximum_benefit_aw_multiple.source_citation)

        if scheme.contributions:
            c = scheme.contributions
            if c.employee_rate:
                _add(sec, "employee_contrib_rate", c.employee_rate.value,
                     c.employee_rate.source_citation)
            if c.employer_rate:
                _add(sec, "employer_contrib_rate", c.employer_rate.value,
                     c.employer_rate.source_citation)
            if c.total_rate:
                _add(sec, "total_contrib_rate", c.total_rate.value, c.total_rate.source_citation)

    ae = params.average_earnings
    _add("average_earnings", "ilostat_series_id", ae.ilostat_series_id or "—")
    _add("average_earnings", "manual_value", ae.manual_value or "—", ae.source_citation)
    _add("average_earnings", "year", ae.year or "")

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Country-level exports
# ---------------------------------------------------------------------------

def export_country_csv(
    results: list[PensionResult],
    iso3: str,
    country_name: str,
    out_dir: Path,
) -> Path:
    """Write the results table to CSV."""
    out_dir.mkdir(parents=True, exist_ok=True)
    df = results_to_df(results, iso3, country_name)
    path = out_dir / f"{iso3}_results.csv"
    df.to_csv(path, index=False)
    logger.info("Exported CSV: %s", path)
    return path


def export_country_excel(
    results: list[PensionResult],
    iso3: str,
    country_name: str,
    params: CountryParams,
    out_dir: Path,
) -> Path:
    """Write a multi-sheet Excel workbook for one country."""
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{iso3}_results.xlsx"

    df_results = results_to_df(results, iso3, country_name)
    df_params = _params_to_df(params)

    # Breakdown sheet: component columns pivoted
    comp_cols = [c for c in df_results.columns if c.startswith("comp_")]
    df_breakdown = df_results[["earnings_multiple"] + comp_cols].copy()
    df_breakdown.columns = ["earnings_multiple"] + [c.replace("comp_", "") for c in comp_cols]

    # Pretty-print rates as percentages
    df_display = df_results.copy()
    for col in ["gross_replacement_rate", "net_replacement_rate",
                "gross_pension_level", "net_pension_level"]:
        if col in df_display.columns:
            df_display[col] = (df_display[col] * 100).round(2)
    # Rename columns for readability
    rename_map = {k: v for k, v in _RESULT_COLUMNS.items() if k in df_display.columns}
    df_display = df_display.rename(columns=rename_map)

    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        df_display.to_excel(writer, sheet_name="Results", index=False)
        df_params.to_excel(writer, sheet_name="Parameters", index=False)
        df_breakdown.to_excel(writer, sheet_name="Component breakdown", index=False)

        # Auto-adjust column widths
        for sheet in writer.sheets.values():
            for col_cells in sheet.columns:
                max_len = max(
                    (len(str(cell.value)) for cell in col_cells if cell.value is not None),
                    default=10,
                )
                sheet.column_dimensions[col_cells[0].column_letter].width = min(max_len + 2, 50)

    logger.info("Exported Excel: %s", path)
    return path


# ---------------------------------------------------------------------------
# Cross-country (Panorama) exports
# ---------------------------------------------------------------------------

def export_panorama_csv(
    all_country_dfs: dict[str, pd.DataFrame],
    out_dir: Path,
    filename: str = "panorama_all_countries.csv",
) -> Path:
    """Stack all country DataFrames and export as a single CSV."""
    out_dir.mkdir(parents=True, exist_ok=True)
    if not all_country_dfs:
        logger.warning("No country data to export.")
        return out_dir / filename
    combined = pd.concat(list(all_country_dfs.values()), ignore_index=True)
    path = out_dir / filename
    combined.to_csv(path, index=False)
    logger.info("Exported Panorama CSV: %s", path)
    return path


def export_panorama_excel(
    all_country_dfs: dict[str, pd.DataFrame],
    out_dir: Path,
    filename: str = "panorama_combined.xlsx",
) -> Path:
    """Write a combined Excel workbook: one sheet per country + comparative sheet."""
    out_dir.mkdir(parents=True, exist_ok=True)
    if not all_country_dfs:
        logger.warning("No country data to export.")
        return out_dir / filename

    path = out_dir / filename
    combined = pd.concat(list(all_country_dfs.values()), ignore_index=True)

    # Build comparative sheet: one row per (iso3, earnings_multiple) with key metrics
    key_cols = [
        "iso3", "country_name", "earnings_multiple",
        "gross_replacement_rate", "net_replacement_rate",
        "gross_pension_level", "net_pension_level",
        "gross_pension_wealth", "net_pension_wealth",
    ]
    comp_cols = [c for c in key_cols if c in combined.columns]
    df_comparative = combined[comp_cols].copy()
    for col in ["gross_replacement_rate", "net_replacement_rate",
                "gross_pension_level", "net_pension_level"]:
        if col in df_comparative.columns:
            df_comparative[col] = (df_comparative[col] * 100).round(2)

    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        df_comparative.to_excel(writer, sheet_name="Comparative", index=False)
        for iso3, df in all_country_dfs.items():
            sheet_name = iso3[:31]  # Excel sheet name limit
            df_copy = df.copy()
            for col in ["gross_replacement_rate", "net_replacement_rate",
                        "gross_pension_level", "net_pension_level"]:
                if col in df_copy.columns:
                    df_copy[col] = (df_copy[col] * 100).round(2)
            df_copy.to_excel(writer, sheet_name=sheet_name, index=False)

        # Auto-adjust column widths
        for sheet in writer.sheets.values():
            for col_cells in sheet.columns:
                max_len = max(
                    (len(str(cell.value)) for cell in col_cells if cell.value is not None),
                    default=10,
                )
                sheet.column_dimensions[col_cells[0].column_letter].width = min(max_len + 2, 40)

    logger.info("Exported Panorama Excel: %s", path)
    return path
