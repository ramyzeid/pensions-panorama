"""Internationalisation strings for the Pensions Panorama dashboard.

Supported languages
-------------------
en – English (default, left-to-right)
ar – Arabic  (right-to-left)

Usage in app.py
---------------
    from pensions_panorama.web.i18n import TRANSLATIONS

    def t(key: str, **kwargs) -> str:
        lang = st.session_state.get("lang", "en")
        text = TRANSLATIONS.get(lang, {}).get(key) or TRANSLATIONS["en"].get(key, key)
        return text.format(**kwargs) if kwargs else text
"""

from __future__ import annotations

TRANSLATIONS: dict[str, dict[str, str]] = {

    # =========================================================================
    # ENGLISH
    # =========================================================================
    "en": {

        # ── Sidebar ──────────────────────────────────────────────────────────
        "app_title": "Pensions Database",
        "app_subtitle": "Comparative pension dataset",
        "reference_year": "Reference year",
        "modeled_sex": "Modeled sex",
        "opt_male": "male",
        "opt_female": "female",
        "opt_all": "all (M+F average)",
        "overview_multiple_caption": "Overview earnings multiple",
        "earnings_multiple_label": "Earnings multiple (×AW)",
        "footer": "v0.1 · data: World Bank, UN WPP, ILOSTAT",
        "language_label": "🌐 Language",
        "loading_spinner": "Loading pension data for all countries…",

        # ── Main tabs ─────────────────────────────────────────────────────────
        "tab_panorama": "🏠 Database",
        "tab_country": "🌍 Country Profile",
        "tab_deep_profile": "📘 Country Deep Profile",
        "tab_compare": "📊 Compare",
        "tab_methodology": "📖 Methodology",
        "tab_pag": "📋 PAG Tables",
        "tab_calculator": "🧮 Pension Calculator",
        "tab_retirement_cost": "💰 Retirement Cost",
        "methodology_section_oecd": "📐 OECD Pension Model",
        "methodology_section_pension_calc": "🧮 Pension Calculator",
        "methodology_section_rc": "💰 Retirement Cost Calculator",
        "tab_glossary": "📖 Glossary",
        "glossary_intro": "Definitions for every indicator, scheme type, and term used across this dashboard.",
        "tab_primer": "🔗 WB Primer Notes",
        "primer_intro": "World Bank Pension Reform Primer — curated reference notes on pension system design, financing, and policy.",
        "deep_profile_header": "Country Deep Profile",
        "deep_profile_last_updated": "Last updated: {date}",
        "deep_profile_narrative_header": "Narrative Overview",
        "deep_profile_country_info_header": "Country Level Information",
        "deep_profile_kpi_header": "{country}'s Pension System",
        "deep_profile_schemes_header": "Main Pension Schemes in the country",
        "deep_profile_indicator_label": "Indicator",
        "deep_profile_indicator_value": "Value",
        "deep_profile_indicator_year": "Year",
        "deep_profile_indicator_source": "Source",
        "not_available": "Not available",

        # ── Retirement Cost tab ───────────────────────────────────────────────
        "rc_header": "💰 Retirement Cost Calculator",
        "rc_subheader": "Estimates annual and lifetime retirement costs using public data (World Bank, WHO, UN WPP).",
        "rc_country": "Country",
        "rc_retirement_age": "Retirement Age",
        "rc_sex": "Sex",
        "rc_scenario": "Scenario",
        "rc_scenario_basic": "Basic",
        "rc_scenario_moderate": "Moderate",
        "rc_scenario_comfortable": "Comfortable",
        "rc_discount_rate": "Real Discount Rate",
        "rc_inflation_rate": "Nominal Inflation Rate",
        "rc_age_uplift": "Health OOP Uplift (unhealthy years)",
        "rc_include_oop": "Include health out-of-pocket spending",
        "rc_use_hale": "Use HALE healthy/unhealthy year split",
        "rc_calculate_btn": "Calculate",
        "rc_calculating": "Fetching data and calculating…",
        "rc_horizon_header": "Retirement Horizon",
        "rc_annual_header": "Annual Cost",
        "rc_lifetime_header": "Lifetime Cost (PV)",
        "rc_monthly_income": "Monthly Income Needed",
        "rc_annual_total": "Annual Total",
        "rc_lifetime_pv": "Lifetime Present Value",
        "rc_healthy_years": "Healthy years",
        "rc_unhealthy_years": "Unhealthy years",
        "rc_horizon_method": "Horizon source",
        "rc_consumption_tier": "Consumption tier",
        "rc_ratio_gdp": "vs GDP per capita",
        "rc_ratio_poverty": "vs Poverty line",
        "rc_ppp_equiv": "PPP equivalent (intl. $)",
        "rc_breakdown_title": "Annual Cost Breakdown",
        "rc_consumption_label": "Consumption",
        "rc_oop_label": "Health OOP",
        "rc_health_years_title": "Retirement Years",
        "rc_sources_header": "Data Sources",
        "rc_proxy_note": "[proxy]",
        "rc_no_le_warning": "No life expectancy data found for this country. Cannot compute lifetime cost.",
        "rc_no_hfce_warning": "No HFCE or poverty line data found. Cannot compute annual consumption target.",
        "rc_disclaimer": "Estimates only. Not financial advice. Data availability varies by country.",
        "rc_tier1": "National Poverty Line",
        "rc_tier3": "Household Consumption (HFCE)",
        "rc_method_wpp": "UN WPP age-specific",
        "rc_method_gho": "WHO GHO HALE at 60 (proxy)",
        "rc_method_none": "Insufficient data",

        # ── Overview tab ──────────────────────────────────────────────────────
        "overview_header": "🏠 Database Overview",
        "kpi_countries": "Countries modeled",
        "kpi_avg_grr": "Avg gross RR @ {n}×AW",
        "kpi_avg_nrr": "Avg net RR @ {n}×AW",
        "kpi_avg_gpw": "Avg gross PW @ {n}×AW",
        "kpi_avg_nra": "Avg NRA (male)",
        "errors_expander": "⚠️ {n} country/countries had load errors",
        "map_metric_label": "Map metric",
        "opt_gross_rr": "Gross RR",
        "opt_net_rr": "Net RR",
        "opt_gross_pl": "Gross PL",
        "opt_net_pl": "Net PL",
        "opt_gross_pw": "Gross PW",
        "map_title_gross_rr": "Gross Replacement Rate @ {n}×AW",
        "map_title_net_rr": "Net Replacement Rate @ {n}×AW",
        "map_title_gross_pl": "Gross Pension Level @ {n}×AW",
        "map_title_net_pl": "Net Pension Level @ {n}×AW",
        "map_title_gross_pw": "Gross Pension Wealth @ {n}×AW",
        "summary_table_header": "Summary Table",
        "col_iso3": "ISO3",
        "col_wb_level": "WB Level",
        "col_gross_rr_at": "Gross RR @ {n}×AW",
        "col_net_rr_at": "Net RR @ {n}×AW",
        "col_gross_pl_at": "Gross PL @ {n}×AW",
        "col_gross_pw_at": "Gross PW @ {n}×AW",
        "no_data_warning": "No country data available.",

        # ── Country Profile tab ───────────────────────────────────────────────
        "country_header": "🌍 Country Profile",
        "select_country": "Select country",
        "metric_country": "Country",
        "metric_nra_mf": "NRA (M / F)",
        "metric_gross_rr_1aw": "Gross RR @ 1×AW",
        "metric_avg_wage": "Avg wage",
        "scheme_details_header": "Pension Scheme Details ({n} scheme)",
        "scheme_details_header_plural": "Pension Scheme Details ({n} schemes)",
        "results_header": "Pension Modeling Results",
        "results_intro": (
            "This table shows the six standard pension indicators, each computed at six different "
            "earnings levels (from half the national average wage up to 2.5 times it). "
            "This lets you see how the pension system treats low earners, average earners, "
            "and high earners differently.\n\n"
            "**How to read the columns:** Each column represents a different type of worker. "
            "For example, **0.5×AW** is someone earning half the national average wage (a low earner), "
            "**1.0×AW** is someone earning exactly the average wage, and **2.5×AW** is a high earner.\n\n"
            "**How to read the rows:**\n"
            "- **Gross replacement rate (%)** — The pension as a percentage of the worker's own "
            "pre-retirement wage, *before* any taxes are deducted. This is the most commonly cited "
            "pension adequacy measure. A value of 60 means the pension replaces 60% of your salary.\n"
            "- **Net replacement rate (%)** — Net pension (after pensioner taxes) divided by *net* "
            "pre-retirement earnings (after worker social contributions and income tax). "
            "Because the denominator is smaller than gross earnings, the net RR can exceed the gross RR "
            "in countries with mandatory employee contributions. This is the OECD standard definition.\n"
            "- **Gross pension level (% AW)** — The pension as a percentage of the *national average "
            "wage*, before taxes. Unlike the replacement rate, this uses a fixed yardstick (the average "
            "wage) so you can compare across countries.\n"
            "- **Net pension level (% AW)** — The after-tax pension as a percentage of the national "
            "average wage.\n"
            "- **Gross pension wealth (×AW)** — The total value of all pension payments you would "
            "receive over your lifetime, expressed as a multiple of the average wage. It accounts for "
            "how long people typically live in retirement. A value of 10 means the lifetime pension pot "
            "equals 10 years of average wages.\n"
            "- **Net pension wealth (×AW)** — The same lifetime value, calculated on after-tax pension amounts."
        ),
        "download_results_csv": "⬇ Download Results CSV",
        "detailed_results_expander": "Detailed results in local currency (absolute amounts)",
        "detailed_results_note": (
            "All pension amounts are in **{currency}** per year. "
            "This table shows the same indicators as above plus the actual currency amounts, "
            "which can help ground the percentages in real money."
        ),
        "col_earnings_aw": "Earnings (×AW)",
        "col_individual_wage": "Individual wage",
        "col_gross_pension": "Gross pension",
        "col_net_pension": "Net pension",
        "col_gross_rr": "Gross RR",
        "col_net_rr": "Net RR",
        "col_gross_pl": "Gross PL",
        "col_net_pl": "Net PL",
        "col_gross_pw": "Gross PW",
        "col_net_pw": "Net PW",
        "charts_header": "Charts",
        "charts_intro": (
            "The six charts below follow the standard layout used in the OECD *Pensions at a Glance* "
            "country notes. Each chart plots a different dimension of pension adequacy against individual "
            "earnings (expressed as a multiple of the national average wage). "
            "Hover over any bar or line to see the exact values."
        ),
        "chart_a_caption": (
            "**a. Gross Pension Level** — How large is the pension relative to the national average wage? "
            "Each coloured segment shows the contribution of one pension scheme (e.g. a flat basic pension "
            "vs an earnings-related scheme). The total bar height is the gross pension level. "
            "A value of 60% means the pension equals 60% of the country's average wage, regardless of "
            "what the individual earned. "
            "*(Calculated as: annual gross pension ÷ national average wage × 100)*"
        ),
        "chart_b_caption": (
            "**b. Gross Replacement Rate** — How much of your own salary does the pension replace? "
            "Each segment again shows one scheme's contribution. The total bar is the gross replacement rate. "
            "A value of 60% means someone earning a certain wage will receive a pension equal to 60% of "
            "that wage. Notice how flat-rate basic pensions create a higher replacement rate for low earners "
            "(the bar is taller on the left) while earnings-related pensions are more equal across earners. "
            "*(Calculated as: annual gross pension ÷ individual pre-retirement wage × 100)*"
        ),
        "chart_c_caption": (
            "**c. Gross and Net Pension Levels** — Compares the pension before tax (gross, solid line) "
            "and after tax (net, dashed line), both expressed as a percentage of average earnings. "
            "Gross pension level = P / AE; net pension level = Pnet / ANE, where ANE is average "
            "earnings *net* of worker social contributions — this is the correct OECD comparison base. "
            "The gap between the two lines shows how much pensioners lose to taxes. "
            "In many countries in this dataset the lines overlap, meaning pensions are tax-free. "
            "The dotted horizontal line marks 100% of average earnings as a reference point. "
            "*(Net PL = Net pension ÷ average net earnings × 100)*"
        ),
        "chart_d_caption": (
            "**d. Gross and Net Replacement Rates** — Compares gross (solid) and net (dashed) "
            "replacement rates against individual earnings. "
            "Gross RR = P / E; Net RR = Pnet / Enet, where Enet = E − worker social contributions. "
            "Because the denominator shrinks (net wage < gross wage), the net RR is often higher than "
            "the gross RR in countries with mandatory EE contributions — you are comparing your pension "
            "to a smaller take-home wage. This is the standard OECD methodology. "
            "*(Net RR = Net pension ÷ net pre-retirement earnings × 100)*"
        ),
        "chart_e_caption": (
            "**e. Taxes Paid by Pensioners and Workers** — Shows effective average burden on each group "
            "as a share of gross earnings (workers) or gross pension (pensioners). "
            "The solid line is the worker total burden: social contributions + any income tax on wages. "
            "This may slope downward at higher earnings when a contribution ceiling applies. "
            "The dashed line is the pensioner total burden: income tax + any social contributions on "
            "pension income. When the worker burden exceeds the pensioner burden, retirement "
            "improves your take-home income beyond just the pension — you also stop paying contributions. "
            "Most countries in this region have zero income tax, so the pensioner line sits at 0%."
        ),
        "chart_f_caption": (
            "**f. Sources of Net Replacement Rate** — Full breakdown of the net replacement rate "
            "(NRR = Pnet / Enet). Each coloured segment shows one scheme's net contribution, "
            "calculated as the scheme's gross pension × (1 − pension tax rate) ÷ net earnings. "
            "Segments are allocated net of pensioner taxes proportionally across schemes (OECD Option 1). "
            "The bars naturally sum to the NRR. When EE contributions are positive, NRR exceeds "
            "GRR because the denominator (Enet) is smaller than gross earnings — this is the "
            "'worker contribution wedge' effect, already embedded in the bar heights. "
            "*(SRC_k = P_k × (1 − t_pension) ÷ Enet; Σ SRC_k = NRR)*"
        ),

        # ── Chart titles and axis labels ─────────────────────────────────────
        "chart_a_title": "a. Gross Pension Level",
        "chart_b_title": "b. Gross Replacement Rate",
        "chart_c_title": "c. Gross and Net Pension Levels",
        "chart_d_title": "d. Gross and Net Replacement Rates",
        "chart_e_title": "e. Taxes Paid by Pensioners and Workers",
        "chart_f_title": "f. Sources of Net Replacement Rate",
        "xaxis_earnings": "Individual earnings (× average wage)",
        "yaxis_gross_pl": "Gross pension level (% average wage)",
        "yaxis_gross_rr": "Gross replacement rate (%)",
        "yaxis_pl": "Pension level (% average wage)",
        "yaxis_rr": "Replacement rate (%)",
        "yaxis_tax_burden": "Tax / contribution burden (% of gross earnings/pension)",
        "yaxis_net_rr": "Net replacement rate (%)",
        "yaxis_pension_wealth": "Pension wealth (× average wage)",
        "trace_gross_pl": "Gross PL",
        "trace_net_pl": "Net PL",
        "trace_gross_rr": "Gross RR",
        "trace_net_rr": "Net RR",
        "trace_gross_pw": "Gross PW",
        "trace_net_pw": "Net PW",
        "trace_worker_ee": "Workers – EE contributions",
        "trace_worker_total": "Workers – total burden (SSC + income tax)",
        "trace_worker_income": "Workers – income tax",
        "trace_pensioner_tax": "Pensioners – income tax",
        "trace_pensioner_total": "Pensioners – total burden (income tax + SSC)",
        "trace_pension_tax_deduction": "Income tax on pension (−)",
        "trace_worker_wedge": "Worker EE contribution wedge (+)",
        "xaxis_earnings_pension": "Individual earnings / pension (× average wage)",
        "annotation_100pct_aw": "100% AW",
        "annotation_100pct": "100%",

        # ── Scheme card ───────────────────────────────────────────────────────
        "label_active": "✅ Active",
        "label_inactive": "⚠️ Inactive / Disrupted",
        "coverage_prefix": "**Coverage:** {text}",
        "section_eligibility": "**Eligibility**",
        "metric_nra_male": "NRA – Male",
        "metric_nra_female": "NRA – Female",
        "metric_era_male": "Early Ret. – Male",
        "metric_era_female": "Early Ret. – Female",
        "metric_min_contrib_yrs": "Min. contribution years",
        "metric_vesting_yrs": "Vesting years",
        "metric_nra_source_m": "NRA source (M)",
        "metric_nra_source_f": "NRA source (F)",
        "section_benefit_formula": "**Benefit Formula**",
        "section_contributions": "**Contributions**",
        "section_notes": "**Notes**",
        "row_accrual_rate": "Accrual rate",
        "row_flat_rate": "Flat rate",
        "row_reference_wage": "Reference wage",
        "row_valorisation": "Valorisation",
        "row_indexation": "Post-ret. indexation",
        "row_min_benefit": "Minimum benefit",
        "row_max_benefit": "Maximum benefit",
        "col_parameter": "Parameter",
        "col_value": "Value",
        "col_source": "Source",
        "col_rate": "Rate",
        "contrib_employee": "Employee rate",
        "contrib_employer": "Employer rate",
        "contrib_total": "Total rate",
        "contrib_ceiling": "Earnings ceiling",
        "contrib_base": "Contribution base",
        "contrib_base_default": "gross wage",
        "non_contributory": "Non-contributory scheme",

        # ── Benefit formula strings ───────────────────────────────────────────
        "ref_career_average": "career-average wage",
        "ref_final_salary": "final salary",
        "ref_average_revalued": "revalued career-average wage",
        "ref_minimum_wage_base": "minimum wage (capped base)",
        "ref_generic": "reference wage",
        "formula_db": "**Pension = {pct:.2f}%** × service years × {ref}",
        "formula_db_min_yrs": "min {yrs} contribution years",
        "formula_db_max": "max {pct:.0f}% AW",
        "formula_db_ceiling": "earnings ceiling {mult:.2f}×AW",
        "formula_db_fallback": "Defined benefit – formula not parameterised",
        "formula_dc": "**Accumulated fund** ({contrib} of wage) → {payout} at NRA {nra}",
        "formula_basic": "**Flat pension = {pct:.1f}%** × average wage (universal, from age {nra})",
        "formula_basic_fallback": "Universal flat-rate pension from age {nra}",
        "formula_minimum": "**Top-up to ≥ {pct:.1f}%** × average wage (applied when earnings-related benefit falls below floor)",
        "formula_minimum_fallback": "Minimum pension guarantee (top-up)",
        "formula_points_value": "Points = (wage / AW) × service years; **Pension = points × point value**",
        "formula_points_accrual": "Points system; effective accrual ≈ **{pct:.2f}%**/yr × {ref}",
        "formula_points_fallback": "Points system – see scheme notes",
        "formula_ndc": "**Notional account** ({contrib} credited at {rate}) ÷ annuity divisor at NRA {nra}",
        "formula_targeted": "**Means-tested: up to {pct:.1f}%** × average wage, phased out above income threshold",
        "formula_targeted_fallback": "Means-tested social pension",
        "formula_generic_fallback": "See scheme notes",
        "unit_yrs": " yrs",
        "nra_delta": "(M {sign}{diff} vs F)",
        "compare_by_multiple": "by earnings multiple",
        "payout_annuity": "annuity",
        "payout_lump_sum": "lump sum",
        "payout_prog_withdrawal": "programmed withdrawal",

        # ── Compare tab ───────────────────────────────────────────────────────
        "compare_header": "📊 Cross-Country Comparison",
        "compare_countries_label": "Countries",
        "compare_metric_label": "Metric",
        "compare_multiple_label": "Earnings multiple",
        "select_one_country": "Select at least one country.",
        "metric_gross_rr_long": "Gross replacement rate",
        "metric_net_rr_long": "Net replacement rate",
        "metric_gross_pl_long": "Gross pension level",
        "metric_net_pl_long": "Net pension level",
        "metric_gross_pw_long": "Gross pension wealth",
        "metric_net_pw_long": "Net pension wealth",
        "comparison_table_header": "Comparison Table",
        "col_country": "Country",

        # ── PAG Tables tab ────────────────────────────────────────────────────
        "pag_header": "📋 PAG-Style Tables",
        "pag_intro": (
            "Comparative tables modeled on the OECD *Pensions at a Glance* publication. "
            "All indicators are computed using the OECD standard methodology (entry age 20, "
            "40-year career, 0.5–2.5×AW earnings multiples)."
        ),
        "pag_tab_21": "2.1 System Structure",
        "pag_tab_3x": "3.1–3.4 Parameters by Region",
        "pag_tab_35": "3.5 Earnings & Valorization",
        "pag_tab_36": "3.6 Indexation",
        "pag_tab_51": "5.1 Gross RR",
        "pag_tab_61": "6.1 Net RR",
        "pag_21_header": "Table 2.1 – Structure of Pension Systems",
        "pag_21_caption": (
            "Classification of mandatory pension schemes by tier and type. "
            "Tier 1 = first-pillar public schemes; Tier 2 = second-pillar mandatory private schemes."
        ),
        "pag_3x_header": "Tables 3.1–3.4 – Summary of Pension System Parameters",
        "pag_3x_region_label": "Filter by World Bank region",
        "pag_3x_all_regions": "All regions",
        "pag_3x_no_data": "No data for selected region.",
        "pag_35_header": "Table 3.5 – Earnings Measure and Valorization",
        "pag_35_caption": "Covers earnings-related schemes (DB, Points, NDC) only.",
        "pag_36_header": "Table 3.6 – Procedures for Adjustment of Pensions in Payment",
        "pag_36_caption": "Indexation method applied to pensions already in payment.",
        "pag_51_header": "Table 5.1 – Gross Replacement Rates by Earnings Level",
        "pag_51_caption": (
            "Mandatory pension (all tiers combined), gross of taxes and contributions. "
            "Individual enters at age 20, retires at the country's normal retirement age."
        ),
        "pag_51_heatmap_title": "**Heat map – Gross Replacement Rate @ 1.0×AW**",
        "pag_61_header": "Table 6.1 – Net Replacement Rates by Earnings Level",
        "pag_61_caption": (
            "Mandatory pension net of income taxes and social contributions on pension income. "
            "Tax treatment is country-specific (see tax parameters in Country Profile)."
        ),
        "pag_61_chart_title": "**Gross vs Net Replacement Rate @ 1.0×AW**",
        "download_csv": "⬇ Download CSV",
        "col_pag_country": "Country",
        "col_pag_iso3": "ISO3",
        "col_pag_region": "Region",
        "col_pag_income": "Income",
        "col_tier1": "Tier 1 (public)",
        "col_tier2": "Tier 2 (private)",
        "col_tier3": "Tier 3 (voluntary)",
        "col_num_schemes": "# Schemes",
        "col_nra_m": "NRA (M)",
        "col_nra_f": "NRA (F)",
        "col_ee_all": "EE % (all)",
        "col_er_all": "ER % (all)",
        "col_scheme": "Scheme",
        "col_tier": "Tier",
        "col_type": "Type",
        "col_min_yrs": "Min yrs",
        "col_vest_yrs": "Vest yrs",
        "col_ee_pct": "EE%",
        "col_er_pct": "ER%",
        "col_total_pct": "Total%",
        "col_ceiling": "Ceiling",
        "col_ceiling_none": "None",
        "col_accrual_yr": "Accrual/yr",
        "col_flat_rate": "Flat rate",
        "col_min_benefit": "Min benefit",
        "col_max_benefit": "Max benefit",
        "col_earnings_measure": "Earnings measure",
        "col_valorization": "Valorization",
        "col_accrual_rate_yr": "Accrual rate/yr",
        "col_indexation": "Indexation",
        "col_indicator": "Indicator",
        "val_career_average": "Career average",
        "val_final_salary": "Final salary",
        "val_revalued_career_avg": "Revalued career avg",
        "val_min_wage_base": "Min-wage base",
        "val_wages": "Wages",
        "val_prices": "Prices",
        "val_gdp": "GDP",
        "val_investment_returns": "Investment returns",
        "val_discretionary": "Discretionary",
        "val_fixed_rate": "Fixed rate",
        "val_prices_cpi": "Prices (CPI)",
        "val_mixed": "Mixed (CPI/wages)",
        "val_na": "—",
        "ind_gross_rr": "Gross replacement rate (%)",
        "ind_net_rr": "Net replacement rate (%)",
        "ind_gross_pl": "Gross pension level (% AW)",
        "ind_net_pl": "Net pension level (% AW)",
        "ind_gross_pw": "Gross pension wealth (×AW)",
        "ind_net_pw": "Net pension wealth (×AW)",
        "pag_gross_rr_pct": "Gross RR @ 1×AW (%)",
        "pag_gross_rr_col": "Gross RR (%)",
        "pag_net_rr_col": "Net RR (%)",
        "chart_rr_xaxis": "Replacement rate (%)",

        # ── Methodology tab ───────────────────────────────────────────────────
        "methodology_header": "📖 Methodology & Data Sources",
        "methodology_body": """
### Modeling approach

The Pensions Database follows the **OECD Pensions at a Glance** methodology:

| Element | Description |
|---|---|
| **Entry age** | 20 |
| **Career length** | 40 years |
| **Contribution density** | 100% of career |
| **Real wage growth** | 2%/yr |
| **Discount rate** | 2% real |
| **DC net real return** | 3%/yr |
| **Post-retirement indexation** | CPI (constant real value) |
| **Pension wealth** | Survival-weighted PV ÷ average wage |

Calculations are performed at **six earnings multiples**: 0.5, 0.75, 1.0, 1.5, 2.0, 2.5 × national average wage.

---

### Indicators

| Indicator | Formula |
|---|---|
| **Gross replacement rate (GRR)** | P(m) ÷ E(m) — gross pension ÷ individual gross earnings |
| **Net replacement rate (NRR)** | Pnet(m) ÷ Enet(m) — net pension ÷ net earnings (after worker SSC + income tax) |
| **Gross pension level (GPL)** | P(m) ÷ AE — gross pension ÷ national average earnings |
| **Net pension level (NPL)** | Pnet(m) ÷ ANE — net pension ÷ average net earnings (AE − worker SSC at 1×AW) |
| **Gross pension wealth (GPW)** | PV(gross benefit stream) ÷ average wage |
| **Net pension wealth (NPW)** | PV(net benefit stream) ÷ average wage |

where: E(m) = m × AE; Enet(m) = E(m) − Tw_ssc(m); ANE = AE − Tw_ssc(1.0×AW); Pnet = P × (1 − t_pension)

---

### Pension scheme types supported

| Type | Description |
|---|---|
| `DB` | Defined-benefit: accrual rate × career years × reference wage |
| `basic` | Flat-rate universal benefit |
| `targeted` | Means-tested social pension (simplified phase-out) |
| `minimum` | Minimum pension guarantee (applied as top-up) |
| `points` | Points system: points = (wage/AW) × years |
| `NDC` | Non-financial defined contribution: notional account ÷ annuity divisor |
| `DC` | Financial defined contribution: accumulated fund converted to annuity |

---

### Data sources

| Layer | Source | API |
|---|---|---|
| **Pension rules** | Human-curated YAML parameter files | — |
| **Average earnings** | ILOSTAT SDMX API (primary); manual values (fallback) | `sdmx.ilo.org/rest` |
| **Life tables** | UN WPP Data Portal (when available) | `population.un.org/dataportalapi` |
| **Macro context** | World Bank Indicators API | `api.worldbank.org/v2` |

---

### Country coverage notes

Several countries (Saudi Arabia, UAE, Kuwait, Qatar, Bahrain, Oman) maintain **dual-track systems**:
national citizens are covered by a mandatory pension fund; expatriate workers (often the majority)
receive only an **End-of-Service Benefit (EOSB)**, a lump-sum gratuity.
This dashboard models the **national citizen scheme only**.

Pakistan's EOBI calculates contributions on the **minimum wage**, not the actual wage, leading
to low effective replacement rates relative to average earnings.

---

### Adding a new country

1. Copy `data/params/_template.yaml` → `data/params/<ISO3>.yaml`
2. Fill all fields; every parameter requires a `source_citation`
3. Run `pp validate-params --countries <ISO3>`
4. Refresh the dashboard — new countries appear automatically
""",

        "methodology_pension_calc_body": """
### Purpose

The **Pension Calculator** estimates the pension benefit for a specific real individual, using the
same scheme rules as the OECD database model but with user-supplied personal inputs instead of
stylized career profiles.

---

### Inputs

| Input | Description |
|---|---|
| **Country** | Determines which scheme rules and average wage to apply |
| **Worker type** | Selects the applicable scheme track (e.g. national citizen, private employee, civil servant) |
| **Sex** | Used for sex-differentiated retirement ages and mortality tables |
| **Current age** | Must be ≥ normal retirement age for eligibility |
| **Service / contribution years** | Verified against minimum service thresholds |
| **Annual wage** | Can be entered in local currency or as a multiple of the national average wage |

---

### Worker types

Each country YAML file defines one or more worker types with a `coverage_status`:

| Status | Meaning |
|---|---|
| `covered` | Mandatory participation; full benefit calculation |
| `excluded` | Not covered by the mandatory scheme (e.g. expatriates in GCC countries); benefit = 0 |
| `unknown` | Coverage unclear; results are indicative only |

Worker types also specify which scheme components apply to them via `scheme_ids`.

---

### Eligibility check

A worker is eligible to receive a pension if **all** of the following are met:
- Current age ≥ Normal Retirement Age (NRA) for their sex
- Service years ≥ minimum contribution / service years (if set)
- Coverage status is not `excluded`

The calculator reports the NRA and how many years remain until eligibility.

---

### Benefit calculation

The engine applies each applicable scheme component in order:

| Scheme type | Formula |
|---|---|
| `DB` | `accrual_rate × min(service_years, max_years) × reference_wage` |
| `basic` | Fixed flat amount (possibly indexed to average wage) |
| `targeted` | `max_benefit − taper_rate × (wage − threshold)` |
| `minimum` | Applied as a top-up if the total benefit falls below the floor |
| `points` | `(wage / AW) × points_per_year × years × point_value` |
| `NDC` | `notional_account_balance / annuity_divisor` |
| `DC` | `accumulated_fund / annuity_divisor` (fund = wage × contrib_rate × years × (1+r)^t) |

Tax is then applied to compute the **net pension**. The **gross replacement rate** is the gross pension
divided by the pre-retirement wage; the **net replacement rate** uses net pension and net wage.

---

### Data sources

| Data | Source |
|---|---|
| Pension scheme rules | Country YAML parameter files (human-curated) |
| National average wage | ILOSTAT SDMX API (primary); manual seed values (fallback) |
| Mortality / survival factors | UN WPP Data Portal |
| Tax rules | Country YAML parameter files |
""",

        "methodology_rc_body": """
### Purpose

The **Retirement Cost Calculator** estimates how much money a person needs to save before retirement
to fund their remaining lifetime — covering basic living expenses and out-of-pocket health spending —
expressed in local currency, PPP-adjusted USD, and as ratios to GDP per capita.

All inputs come from publicly accessible APIs; every figure is cited.

---

### Step 1 — Retirement horizon

The number of years of retirement is estimated from **remaining life expectancy at the retirement age**,
using a priority fallback chain:

| Priority | Source | Method |
|---|---|---|
| 1 (primary) | UN WPP Data Portal — indicator 75 | Age-specific remaining LE at exact retirement age, most recent 2020–2030 projection |
| 2 (proxy) | WHO GHO — `WHOSIS_000007` | HALE at 60; used as a proxy when UN WPP data is unavailable |
| 3 (insufficient) | — | No life-expectancy data available; lifetime cost cannot be computed |

---

### Step 2 — HALE split (healthy vs unhealthy years)

When **Use HALE split** is enabled, the retirement horizon is divided into:

- **Healthy years** = HALE at retirement age (from WHO GHO)
- **Unhealthy years** = Total horizon − Healthy years

Unhealthy years attract higher health spending (see Step 4).

> HALE at 60 from WHO GHO is rescaled proportionally when the retirement age differs from 60.

---

### Step 3 — Annual consumption target

The baseline living cost is set using a **tiered approach**:

| Tier | Source | When used |
|---|---|---|
| **Tier 1** | National poverty line × scenario multiplier | When a country-specific poverty line is seeded in the database |
| **Tier 3** | HFCE per capita (local currency) × scenario multiplier | Default for all countries |

**Scenario multipliers applied to HFCE per capita (Tier 3):**

| Scenario | Multiplier | Rationale |
|---|---|---|
| Basic | 0.55 × HFCE/capita | Subsistence-level spending |
| Moderate | 0.75 × HFCE/capita | Modest comfort; default |
| Comfortable | 1.00 × HFCE/capita | Maintaining pre-retirement lifestyle |

HFCE per capita in local currency = WDI `NE.CON.PRVT.PC.KD` (constant 2015 USD) × PPP factor (`PA.NUS.PPP`).

---

### Step 4 — Annual health out-of-pocket (OOP) spending

**Baseline OOP** = (`SH.XPD.OOPC.CH.ZS` / 100) × `SH.XPD.CHEX.PC.CD` × PPP factor

With HALE split enabled, the annual OOP is a weighted average:

```
Annual OOP = (healthy_years × baseline_OOP + unhealthy_years × baseline_OOP × age_uplift_factor)
             ÷ total_horizon
```

The **age uplift factor** (default 1.5×) reflects higher healthcare utilisation in years of poor health.
Set it to 1.0 to apply a flat rate regardless of health status.

---

### Step 5 — Lifetime present value

Total annual cost = consumption target + health OOP (if enabled).

The **present value of lifetime cost** is computed as:

```
PV = Σ_{t=1}^{H}  [annual_cost × (1 + g)^(t−1)] / (1 + r)^t
```

where:
- `H` = retirement horizon (years)
- `g` = nominal inflation rate (adjusts future costs upward)
- `r` = nominal discount rate (adjusts future costs to today's value)

The **required monthly income** to fund retirement is `PV ÷ (H × 12)`.

---

### Benchmark ratios

| Ratio | Formula |
|---|---|
| **× GDP per capita** | Annual total cost ÷ GDP per capita (WDI `NY.GDP.PCAP.CD`) |
| **PPP-USD equivalent** | Annual total cost ÷ PPP factor |
| **× Poverty line** | Annual total cost ÷ international poverty line in local currency |

---

### Data sources

| Indicator | WDI code | Used for |
|---|---|---|
| HFCE per capita (2015 USD) | `NE.CON.PRVT.PC.KD` | Consumption baseline (Tier 3) |
| Current health expenditure per capita | `SH.XPD.CHEX.PC.CD` | Health OOP baseline |
| OOP as % of CHE | `SH.XPD.OOPC.CH.ZS` | Health OOP baseline |
| PPP conversion factor | `PA.NUS.PPP` | Local currency conversion |
| GDP per capita (USD) | `NY.GDP.PCAP.CD` | Benchmark ratio |
| HALE at 60 (total) | WHO GHO `WHOSIS_000007` | Healthy/unhealthy year split |
| Age-specific LE | UN WPP indicator 75 | Retirement horizon |

---

### Limitations and caveats

- Costs are expressed in **today's local currency** (real terms); the PV calculation then applies
  inflation and discounting to convert to a comparable single figure.
- Health OOP data from WDI reflects **population-average** spending, not retiree-specific rates.
- Tier 2 (World Bank PIP poverty lines) is not used: PIP returns empty data for most countries in scope.
- Results are **estimates** intended for comparative illustration, not financial planning advice.
""",
    },

    # =========================================================================
    # ARABIC
    # =========================================================================
    "ar": {

        # ── Sidebar ──────────────────────────────────────────────────────────
        "app_title": "قاعدة بيانات المعاشات التقاعدية",
        "app_subtitle": "بيانات مقارنة لأنظمة التقاعد",
        "reference_year": "السنة المرجعية",
        "modeled_sex": "الجنس المُحاكى",
        "opt_male": "ذكر",
        "opt_female": "أنثى",
        "opt_all": "كلاهما (متوسط ذ+أ)",
        "overview_multiple_caption": "مضاعف الدخل للنظرة العامة",
        "earnings_multiple_label": "مضاعف الدخل (×متوسط الأجر)",
        "footer": "الإصدار 0.1 · البيانات: البنك الدولي، UN WPP، ILOSTAT",
        "language_label": "🌐 اللغة",
        "loading_spinner": "جارٍ تحميل بيانات المعاشات لجميع الدول…",

        # ── Main tabs ─────────────────────────────────────────────────────────
        "tab_panorama": "🏠 النظرة العامة",
        "tab_country": "🌍 ملف الدولة",
        "tab_deep_profile": "📘 الملف المتعمق للدولة",
        "tab_compare": "📊 المقارنة",
        "tab_methodology": "📖 المنهجية",
        "tab_pag": "📋 جداول PAG",
        "tab_calculator": "🧮 حاسبة المعاش",
        "tab_retirement_cost": "💰 تكلفة التقاعد",
        "methodology_section_oecd": "📐 نموذج OECD للمعاشات",
        "methodology_section_pension_calc": "🧮 حاسبة المعاش الشخصية",
        "methodology_section_rc": "💰 حاسبة تكلفة التقاعد",
        "tab_glossary": "📖 المصطلحات",
        "glossary_intro": "تعريفات لجميع المؤشرات وأنواع الأنظمة والمصطلحات المستخدمة في لوحة المعلومات.",
        "tab_primer": "🔗 ملاحظات البنك الدولي",
        "primer_intro": "ملاحظات البنك الدولي حول إصلاح المعاشات — مراجع منتقاة حول تصميم أنظمة التقاعد وتمويلها وسياساتها.",
        "deep_profile_header": "الملف المتعمق للدولة",
        "deep_profile_last_updated": "آخر تحديث: {date}",
        "deep_profile_narrative_header": "نظرة سردية عامة",
        "deep_profile_country_info_header": "معلومات على مستوى الدولة",
        "deep_profile_kpi_header": "نظام التقاعد في {country}",
        "deep_profile_schemes_header": "أهم برامج التقاعد في الدولة",
        "deep_profile_indicator_label": "المؤشر",
        "deep_profile_indicator_value": "القيمة",
        "deep_profile_indicator_year": "السنة",
        "deep_profile_indicator_source": "المصدر",
        "not_available": "غير متوفر",

        # ── Retirement Cost tab (Arabic) ──────────────────────────────────────
        "rc_header": "💰 حاسبة تكلفة التقاعد",
        "rc_subheader": "تقدير التكاليف السنوية ومدى الحياة للتقاعد باستخدام بيانات عامة (البنك الدولي، منظمة الصحة العالمية، UN WPP).",
        "rc_country": "الدولة",
        "rc_retirement_age": "سن التقاعد",
        "rc_sex": "الجنس",
        "rc_scenario": "السيناريو",
        "rc_scenario_basic": "أساسي",
        "rc_scenario_moderate": "معتدل",
        "rc_scenario_comfortable": "مريح",
        "rc_discount_rate": "معدل الخصم الحقيقي",
        "rc_inflation_rate": "معدل التضخم الاسمي",
        "rc_age_uplift": "معامل رفع النفقات الصحية (سنوات المرض)",
        "rc_include_oop": "تضمين الإنفاق الصحي من الجيب",
        "rc_use_hale": "استخدام تقسيم HALE للسنوات الصحية/المرضية",
        "rc_calculate_btn": "احسب",
        "rc_calculating": "جارٍ جلب البيانات والحساب…",
        "rc_horizon_header": "أفق التقاعد",
        "rc_annual_header": "التكلفة السنوية",
        "rc_lifetime_header": "تكلفة العمر (القيمة الحالية)",
        "rc_monthly_income": "الدخل الشهري المطلوب",
        "rc_annual_total": "الإجمالي السنوي",
        "rc_lifetime_pv": "القيمة الحالية مدى الحياة",
        "rc_healthy_years": "سنوات الصحة",
        "rc_unhealthy_years": "سنوات المرض",
        "rc_horizon_method": "مصدر الأفق",
        "rc_consumption_tier": "مستوى الاستهلاك",
        "rc_ratio_gdp": "مقارنة بنصيب الفرد من الناتج المحلي",
        "rc_ratio_poverty": "مقارنة بخط الفقر",
        "rc_ppp_equiv": "المعادل بالدولار الدولي (تعادل القوة الشرائية)",
        "rc_breakdown_title": "تفصيل التكلفة السنوية",
        "rc_consumption_label": "الاستهلاك",
        "rc_oop_label": "الإنفاق الصحي من الجيب",
        "rc_health_years_title": "سنوات التقاعد",
        "rc_sources_header": "مصادر البيانات",
        "rc_proxy_note": "[بديل]",
        "rc_no_le_warning": "لا توجد بيانات لأمد الحياة لهذه الدولة. لا يمكن احتساب التكلفة مدى الحياة.",
        "rc_no_hfce_warning": "لا توجد بيانات HFCE أو خط فقر. لا يمكن احتساب هدف الاستهلاك السنوي.",
        "rc_disclaimer": "تقديرات فقط. ليست نصيحة مالية. توافر البيانات يتفاوت حسب الدولة.",
        "rc_tier1": "خط الفقر الوطني",
        "rc_tier3": "الاستهلاك الأسري (HFCE)",
        "rc_method_wpp": "UN WPP (محدد السن)",
        "rc_method_gho": "HALE منظمة الصحة العالمية عند 60 (بديل)",
        "rc_method_none": "بيانات غير كافية",

        # ── Overview tab ──────────────────────────────────────────────────────
        "overview_header": "🏠 النظرة العامة على المعاشات",
        "kpi_countries": "عدد الدول المحاكاة",
        "kpi_avg_grr": "متوسط معدل الإحلال الإجمالي @ {n}×AW",
        "kpi_avg_nrr": "متوسط معدل الإحلال الصافي @ {n}×AW",
        "kpi_avg_gpw": "متوسط الثروة التقاعدية الإجمالية @ {n}×AW",
        "kpi_avg_nra": "متوسط سن التقاعد (ذكور)",
        "errors_expander": "⚠️ {n} دولة/دول واجهت أخطاء في التحميل",
        "map_metric_label": "مؤشر الخريطة",
        "opt_gross_rr": "معدل الإحلال الإجمالي",
        "opt_net_rr": "معدل الإحلال الصافي",
        "opt_gross_pl": "مستوى المعاش الإجمالي",
        "opt_net_pl": "مستوى المعاش الصافي",
        "opt_gross_pw": "الثروة التقاعدية الإجمالية",
        "map_title_gross_rr": "معدل الإحلال الإجمالي @ {n}×متوسط الأجر",
        "map_title_net_rr": "معدل الإحلال الصافي @ {n}×متوسط الأجر",
        "map_title_gross_pl": "مستوى المعاش الإجمالي @ {n}×متوسط الأجر",
        "map_title_net_pl": "مستوى المعاش الصافي @ {n}×متوسط الأجر",
        "map_title_gross_pw": "الثروة التقاعدية الإجمالية @ {n}×متوسط الأجر",
        "summary_table_header": "جدول الملخص",
        "col_iso3": "رمز الدولة",
        "col_wb_level": "مستوى البنك الدولي",
        "col_gross_rr_at": "معدل الإحلال الإجمالي @ {n}×AW",
        "col_net_rr_at": "معدل الإحلال الصافي @ {n}×AW",
        "col_gross_pl_at": "مستوى المعاش الإجمالي @ {n}×AW",
        "col_gross_pw_at": "الثروة التقاعدية الإجمالية @ {n}×AW",
        "no_data_warning": "لا توجد بيانات متاحة.",

        # ── Country Profile tab ───────────────────────────────────────────────
        "country_header": "🌍 ملف الدولة",
        "select_country": "اختر الدولة",
        "metric_country": "الدولة",
        "metric_nra_mf": "سن التقاعد (ذ / أ)",
        "metric_gross_rr_1aw": "معدل الإحلال الإجمالي @ 1×AW",
        "metric_avg_wage": "متوسط الأجر",
        "scheme_details_header": "تفاصيل نظام التقاعد ({n} نظام)",
        "scheme_details_header_plural": "تفاصيل أنظمة التقاعد ({n} أنظمة)",
        "results_header": "نتائج محاكاة المعاشات",
        "results_intro": (
            "يعرض هذا الجدول ستة مؤشرات تقاعدية معيارية، محسوبة عند ستة مستويات من الدخل "
            "(تتراوح بين نصف متوسط الأجر الوطني وضعفيه ونصف). يتيح ذلك رؤية كيفية تعامل نظام "
            "التقاعد مع محدودي الدخل ومتوسطيه ومرتفعيه على حدٍّ سواء.\n\n"
            "**كيفية قراءة الأعمدة:** كل عمود يمثل نوعاً مختلفاً من العمال. على سبيل المثال، "
            "**0.5×AW** هو شخص يكسب نصف متوسط الأجر الوطني (دخل منخفض)، **1.0×AW** يكسب "
            "المتوسط بالضبط، و**2.5×AW** دخل مرتفع.\n\n"
            "**كيفية قراءة الصفوف:**\n"
            "- **معدل الإحلال الإجمالي (%)** — المعاش كنسبة من أجر الفرد قبل التقاعد، قبل اقتطاع "
            "أي ضرائب. هذا هو المؤشر الأكثر شيوعاً لقياس كفاية المعاش. قيمة 60 تعني أن المعاش "
            "يعوّض 60% من الراتب.\n"
            "- **معدل الإحلال الصافي (%)** — النسبة ذاتها، لكن بعد خصم ضريبة الدخل على المعاش. "
            "هذا هو ما تستلمه فعلياً مقارنةً بما كنت تكسبه.\n"
            "- **مستوى المعاش الإجمالي (% من متوسط الأجر)** — المعاش كنسبة من متوسط الأجر "
            "الوطني، قبل الضريبة. يتيح المقارنة بين الدول لأنه يستخدم مقياساً ثابتاً.\n"
            "- **مستوى المعاش الصافي (% من متوسط الأجر)** — المعاش بعد الضريبة كنسبة من متوسط "
            "الأجر الوطني.\n"
            "- **الثروة التقاعدية الإجمالية (× متوسط الأجر)** — القيمة الإجمالية لجميع مدفوعات "
            "المعاش على مدى حياة المتقاعد، معبّراً عنها بمضاعفات متوسط الأجر. قيمة 10 تعني أن "
            "مجموع المعاشات يعادل 10 سنوات من متوسط الأجر.\n"
            "- **الثروة التقاعدية الصافية (× متوسط الأجر)** — القيمة الإجمالية ذاتها، محسوبة على "
            "أساس المعاش بعد الضريبة."
        ),
        "download_results_csv": "⬇ تحميل النتائج (CSV)",
        "detailed_results_expander": "نتائج تفصيلية بالعملة المحلية (المبالغ الفعلية)",
        "detailed_results_note": (
            "جميع مبالغ المعاشات بالوحدة **{currency}** سنوياً. "
            "يعرض هذا الجدول المؤشرات ذاتها مع المبالغ الفعلية بالعملة المحلية، "
            "مما يساعد على تحويل النسب المئوية إلى أرقام ملموسة."
        ),
        "col_earnings_aw": "الدخل (×متوسط الأجر)",
        "col_individual_wage": "أجر الفرد",
        "col_gross_pension": "المعاش الإجمالي",
        "col_net_pension": "المعاش الصافي",
        "col_gross_rr": "معدل الإحلال الإجمالي",
        "col_net_rr": "معدل الإحلال الصافي",
        "col_gross_pl": "مستوى المعاش الإجمالي",
        "col_net_pl": "مستوى المعاش الصافي",
        "col_gross_pw": "الثروة التقاعدية الإجمالية",
        "col_net_pw": "الثروة التقاعدية الصافية",
        "charts_header": "الرسوم البيانية",
        "charts_intro": (
            "تتبع الرسوم البيانية الست أدناه التخطيط المعياري المستخدم في تقرير منظمة التعاون "
            "الاقتصادي والتنمية (OECD) 'المعاشات في لمحة'. يرسم كل مخطط بُعداً مختلفاً لكفاية "
            "المعاش مقابل دخل الفرد (معبَّراً عنه كمضاعف لمتوسط الأجر الوطني). "
            "مرّر المؤشر فوق أي شريط أو خط لرؤية القيم الدقيقة."
        ),
        "chart_a_caption": (
            "**أ. مستوى المعاش الإجمالي** — يجيب هذا الرسم عن السؤال: ما حجم المعاش مقارنةً بمتوسط "
            "الأجر الوطني؟ يمثل كل لون شريحةً من نظام تقاعدي محدد (مثل معاش أساسي ثابت أو معاش "
            "مرتبط بالأجر). ارتفاع الشريط الإجمالي يعكس مستوى المعاش الإجمالي. قيمة 60% تعني أن "
            "المعاش يساوي 60% من متوسط الأجور في البلاد، بصرف النظر عن دخل الفرد. "
            "*(طريقة الحساب: المعاش السنوي الإجمالي ÷ متوسط الأجر الوطني × 100)*"
        ),
        "chart_b_caption": (
            "**ب. معدل الإحلال الإجمالي** — يبيّن هذا الرسم: بأي نسبة يعوّض المعاش راتبك قبل التقاعد؟ "
            "يمثل كل لون إسهام نظام تقاعدي واحد. قيمة 60% تعني أن من كان راتبه 10,000 سيحصل على "
            "معاش بقيمة 6,000. لاحظ أن المعاشات الأساسية الثابتة تمنح نسبة إحلال أعلى لمحدودي الدخل "
            "(الأشرطة أطول على اليسار)، بينما المعاشات المرتبطة بالأجر أكثر تناسباً مع جميع الفئات. "
            "*(طريقة الحساب: المعاش السنوي الإجمالي ÷ أجر الفرد قبل التقاعد × 100)*"
        ),
        "chart_c_caption": (
            "**ج. مستوى المعاش الإجمالي والصافي** — يقارن هذا الرسم بين المعاش قبل الضريبة (الإجمالي، "
            "الخط الصلب) وبعد الضريبة (الصافي، الخط المتقطع). "
            "مستوى المعاش الإجمالي = P ÷ AE؛ مستوى المعاش الصافي = Pnet ÷ ANE، حيث ANE هو "
            "متوسط الأجر صافياً من اشتراكات الموظف — وهذا هو القياس المعياري لمنظمة OECD. "
            "الفجوة بين الخطين تُجسّد الاقتطاع الضريبي. في كثير من دول المنطقة يتطابق الخطان. "
            "*(مستوى المعاش الصافي = المعاش الصافي ÷ متوسط الأجر الصافي × 100)*"
        ),
        "chart_d_caption": (
            "**د. معدل الإحلال الإجمالي والصافي** — يقارن معدل الإحلال الإجمالي (الخط الصلب) "
            "والصافي (الخط المتقطع). معدل الإحلال الإجمالي = P ÷ E؛ "
            "معدل الإحلال الصافي = Pnet ÷ Enet، حيث Enet = E − اشتراكات الموظف. "
            "نظراً لأن المقام (صافي الأجر) أصغر من الأجر الإجمالي، قد يتجاوز معدل الإحلال الصافي "
            "الإجمالي في الدول ذات اشتراكات إلزامية — وهذا تعريف منظمة OECD الصحيح. "
            "*(معدل الإحلال الصافي = المعاش الصافي ÷ الأجر الصافي قبل التقاعد × 100)*"
        ),
        "chart_e_caption": (
            "**هـ. الضرائب والاشتراكات على العمال والمتقاعدين** — يعرض معدل العبء الفعلي المتوسط "
            "لكل فريق كنسبة من الأجر الإجمالي (العمال) أو المعاش الإجمالي (المتقاعدون). "
            "الخط الصلب يمثل إجمالي عبء العمال: اشتراكات اجتماعية وأي ضريبة دخل على الأجر. "
            "قد ينخفض عند الدخول المرتفعة إذا وُجد سقف للاشتراكات. "
            "الخط المتقطع يمثل إجمالي عبء المتقاعدين: ضريبة الدخل وأي اشتراكات على المعاش. "
            "حين يتجاوز عبء العامل عبء المتقاعد، يتحسّن الدخل الصافي بعد التقاعد. "
            "كثير من دول المنطقة لا تفرض ضريبة دخل، لذا يبقى خط المتقاعد عند الصفر."
        ),
        "chart_f_caption": (
            "**و. مصادر معدل الإحلال الصافي** — يفكّك هذا الرسم معدل الإحلال الصافي "
            "(NRR = Pnet ÷ Enet) إلى إسهام كل نظام تقاعدي. "
            "كل شريح يمثل: معاش النظام × (1 − معدل الضريبة على المعاش) ÷ الأجر الصافي. "
            "تُوزَّع الضرائب على المعاش تناسبياً بين الأنظمة (خيار OECD الأول). "
            "مجموع الأشرطة يساوي تماماً معدل الإحلال الصافي. وحين تكون اشتراكات الموظف موجبة، "
            "ترتفع الأشرطة فوق معدل الإحلال الإجمالي لأن المقام صغر — وهذا هو 'أثر اشتراكات العامل' "
            "المُضمَّن تلقائياً في الأرقام. "
            "*(SRC_k = P_k × (1 − t) ÷ Enet؛ Σ SRC_k = معدل الإحلال الصافي)*"
        ),

        # ── Chart titles and axis labels ─────────────────────────────────────
        "chart_a_title": "أ. مستوى المعاش الإجمالي",
        "chart_b_title": "ب. معدل الإحلال الإجمالي",
        "chart_c_title": "ج. مستوى المعاش الإجمالي والصافي",
        "chart_d_title": "د. معدل الإحلال الإجمالي والصافي",
        "chart_e_title": "هـ. الضرائب والاشتراكات على العمال والمتقاعدين",
        "chart_f_title": "و. مصادر معدل الإحلال الصافي",
        "xaxis_earnings": "دخل الفرد (× متوسط الأجر)",
        "yaxis_gross_pl": "مستوى المعاش الإجمالي (% من متوسط الأجر)",
        "yaxis_gross_rr": "معدل الإحلال الإجمالي (%)",
        "yaxis_pl": "مستوى المعاش (% من متوسط الأجر)",
        "yaxis_rr": "معدل الإحلال (%)",
        "yaxis_tax_burden": "عبء الضرائب والاشتراكات (% من الأجر/المعاش الإجمالي)",
        "yaxis_net_rr": "معدل الإحلال الصافي (%)",
        "yaxis_pension_wealth": "الثروة التقاعدية (× متوسط الأجر)",
        "trace_gross_pl": "مستوى المعاش الإجمالي",
        "trace_net_pl": "مستوى المعاش الصافي",
        "trace_gross_rr": "معدل الإحلال الإجمالي",
        "trace_net_rr": "معدل الإحلال الصافي",
        "trace_gross_pw": "الثروة التقاعدية الإجمالية",
        "trace_net_pw": "الثروة التقاعدية الصافية",
        "trace_worker_ee": "العمال – اشتراكات التأمين الاجتماعي",
        "trace_worker_total": "العمال – إجمالي العبء (اشتراكات + ضريبة)",
        "trace_worker_income": "العمال – ضريبة الدخل",
        "trace_pensioner_tax": "المتقاعدون – ضريبة الدخل",
        "trace_pensioner_total": "المتقاعدون – إجمالي العبء (ضريبة + اشتراكات)",
        "trace_pension_tax_deduction": "ضريبة الدخل على المعاش (−)",
        "trace_worker_wedge": "أثر اشتراكات العامل (+)",
        "xaxis_earnings_pension": "دخل الفرد / المعاش (× متوسط الأجر)",
        "annotation_100pct_aw": "100% من متوسط الأجر",
        "annotation_100pct": "100%",

        # ── Scheme card ───────────────────────────────────────────────────────
        "label_active": "✅ نشط",
        "label_inactive": "⚠️ غير نشط / متوقف",
        "coverage_prefix": "**نطاق التغطية:** {text}",
        "section_eligibility": "**شروط الأهلية**",
        "metric_nra_male": "سن التقاعد – ذكور",
        "metric_nra_female": "سن التقاعد – إناث",
        "metric_era_male": "التقاعد المبكر – ذكور",
        "metric_era_female": "التقاعد المبكر – إناث",
        "metric_min_contrib_yrs": "الحد الأدنى لسنوات المساهمة",
        "metric_vesting_yrs": "سنوات الاستحقاق الكامل",
        "metric_nra_source_m": "مصدر سن التقاعد (ذ)",
        "metric_nra_source_f": "مصدر سن التقاعد (أ)",
        "section_benefit_formula": "**صيغة المزايا**",
        "section_contributions": "**الاشتراكات**",
        "section_notes": "**ملاحظات**",
        "row_accrual_rate": "معدل الاستحقاق السنوي",
        "row_flat_rate": "معدل ثابت",
        "row_reference_wage": "الأجر المرجعي",
        "row_valorisation": "مؤشرة الاستحقاق",
        "row_indexation": "مؤشرة ما بعد التقاعد",
        "row_min_benefit": "الحد الأدنى للمزايا",
        "row_max_benefit": "الحد الأقصى للمزايا",
        "col_parameter": "المعامل",
        "col_value": "القيمة",
        "col_source": "المصدر",
        "col_rate": "المعدل",
        "contrib_employee": "معدل اشتراك الموظف",
        "contrib_employer": "معدل اشتراك صاحب العمل",
        "contrib_total": "إجمالي معدل الاشتراك",
        "contrib_ceiling": "سقف الأجر الخاضع للاشتراك",
        "contrib_base": "وعاء الاشتراك",
        "contrib_base_default": "الأجر الإجمالي",
        "non_contributory": "نظام غير اشتراكي",

        # ── Benefit formula strings ───────────────────────────────────────────
        "ref_career_average": "متوسط أجر المسيرة المهنية",
        "ref_final_salary": "الراتب الأخير",
        "ref_average_revalued": "متوسط الأجر المعدَّل",
        "ref_minimum_wage_base": "الحد الأدنى للأجور (أساس محدود)",
        "ref_generic": "الأجر المرجعي",
        "formula_db": "**المعاش = {pct:.2f}%** × سنوات الخدمة × {ref}",
        "formula_db_min_yrs": "حد أدنى {yrs} سنة مساهمة",
        "formula_db_max": "حد أقصى {pct:.0f}% من متوسط الأجر",
        "formula_db_ceiling": "سقف الأجر {mult:.2f}×متوسط الأجر",
        "formula_db_fallback": "معاش محدد المزايا – الصيغة غير مُعرَّفة",
        "formula_dc": "**صندوق متراكم** ({contrib} من الأجر) ← {payout} عند بلوغ سن التقاعد {nra}",
        "formula_basic": "**معاش ثابت = {pct:.1f}%** × متوسط الأجر (شامل، من سن {nra})",
        "formula_basic_fallback": "معاش أساسي ثابت من سن {nra}",
        "formula_minimum": "**دعم لضمان ≥ {pct:.1f}%** × متوسط الأجر (يُطبَّق عند انخفاض المعاش المرتبط بالأجر عن الحد)",
        "formula_minimum_fallback": "ضمان الحد الأدنى للمعاش",
        "formula_points_value": "النقاط = (الأجر ÷ متوسط الأجر) × سنوات الخدمة؛ **المعاش = النقاط × قيمة النقطة**",
        "formula_points_accrual": "نظام نقاط؛ استحقاق فعلي ≈ **{pct:.2f}%**/سنة × {ref}",
        "formula_points_fallback": "نظام نقاط – انظر ملاحظات النظام",
        "formula_ndc": "**حساب اسمي** ({contrib} مُضافة بمعدل {rate}) ÷ معامل الأقساط عند سن التقاعد {nra}",
        "formula_targeted": "**مُختبَر الدخل: حتى {pct:.1f}%** × متوسط الأجر، يتناقص مع ارتفاع الدخل",
        "formula_targeted_fallback": "معاش اجتماعي مُختبَر الدخل",
        "formula_generic_fallback": "انظر ملاحظات النظام",
        "unit_yrs": " سنة",
        "nra_delta": "(ذ {sign}{diff} مقابل أ)",
        "compare_by_multiple": "حسب مضاعف الدخل",
        "payout_annuity": "قسط سنوي",
        "payout_lump_sum": "مبلغ مقطوع",
        "payout_prog_withdrawal": "سحب تدريجي",

        # ── Compare tab ───────────────────────────────────────────────────────
        "compare_header": "📊 المقارنة بين الدول",
        "compare_countries_label": "الدول",
        "compare_metric_label": "المؤشر",
        "compare_multiple_label": "مضاعف الدخل",
        "select_one_country": "اختر دولة واحدة على الأقل.",
        "metric_gross_rr_long": "معدل الإحلال الإجمالي",
        "metric_net_rr_long": "معدل الإحلال الصافي",
        "metric_gross_pl_long": "مستوى المعاش الإجمالي",
        "metric_net_pl_long": "مستوى المعاش الصافي",
        "metric_gross_pw_long": "الثروة التقاعدية الإجمالية",
        "metric_net_pw_long": "الثروة التقاعدية الصافية",
        "comparison_table_header": "جدول المقارنة",
        "col_country": "الدولة",

        # ── PAG Tables tab ────────────────────────────────────────────────────
        "pag_header": "📋 جداول على غرار PAG",
        "pag_intro": (
            "جداول مقارنة مستوحاة من تقرير منظمة OECD 'المعاشات في لمحة'. "
            "تُحسب جميع المؤشرات وفق المنهجية المعيارية لمنظمة OECD (سن الدخول 20 عاماً، "
            "مسيرة مهنية 40 عاماً، مضاعفات الدخل من 0.5 إلى 2.5×متوسط الأجر)."
        ),
        "pag_tab_21": "2.1 هيكل النظام",
        "pag_tab_3x": "3.1–3.4 معاملات المنطقة",
        "pag_tab_35": "3.5 الأجر والمؤشرة",
        "pag_tab_36": "3.6 المؤشرة بعد التقاعد",
        "pag_tab_51": "5.1 معدل الإحلال الإجمالي",
        "pag_tab_61": "6.1 معدل الإحلال الصافي",
        "pag_21_header": "الجدول 2.1 – هيكل أنظمة التقاعد",
        "pag_21_caption": (
            "تصنيف أنظمة التقاعد الإلزامية حسب المستوى والنوع. "
            "المستوى 1 = الأنظمة العامة للركيزة الأولى؛ المستوى 2 = الأنظمة الخاصة الإلزامية."
        ),
        "pag_3x_header": "الجداول 3.1–3.4 – ملخص معاملات نظام التقاعد",
        "pag_3x_region_label": "تصفية حسب منطقة البنك الدولي",
        "pag_3x_all_regions": "جميع المناطق",
        "pag_3x_no_data": "لا توجد بيانات للمنطقة المختارة.",
        "pag_35_header": "الجدول 3.5 – مقياس الأجر ومؤشرة الاستحقاق",
        "pag_35_caption": "يشمل الأنظمة المرتبطة بالأجر فقط (محدد المزايا، نقاط، اسمي).",
        "pag_36_header": "الجدول 3.6 – إجراءات تعديل المعاشات بعد التقاعد",
        "pag_36_caption": "آلية المؤشرة المطبّقة على المعاشات في مرحلة الصرف.",
        "pag_51_header": "الجدول 5.1 – معدلات الإحلال الإجمالية حسب مستوى الدخل",
        "pag_51_caption": (
            "معاش إلزامي (جميع المستويات مجتمعة)، إجمالي قبل الضرائب والاشتراكات. "
            "يدخل الفرد سوق العمل في سن 20 ويتقاعد عند بلوغ سن التقاعد الاعتيادي للبلد."
        ),
        "pag_51_heatmap_title": "**خريطة حرارية – معدل الإحلال الإجمالي @ 1.0×متوسط الأجر**",
        "pag_61_header": "الجدول 6.1 – معدلات الإحلال الصافية حسب مستوى الدخل",
        "pag_61_caption": (
            "معاش إلزامي صافٍ بعد ضريبة الدخل والاشتراكات الاجتماعية على دخل المعاش. "
            "المعاملة الضريبية خاصة بكل دولة (انظر معاملات الضريبة في ملف الدولة)."
        ),
        "pag_61_chart_title": "**معدل الإحلال الإجمالي مقابل الصافي @ 1.0×متوسط الأجر**",
        "download_csv": "⬇ تحميل CSV",
        "col_pag_country": "الدولة",
        "col_pag_iso3": "رمز ISO",
        "col_pag_region": "المنطقة",
        "col_pag_income": "مستوى الدخل",
        "col_tier1": "المستوى 1 (عام)",
        "col_tier2": "المستوى 2 (خاص)",
        "col_tier3": "المستوى 3 (اختياري)",
        "col_num_schemes": "عدد الأنظمة",
        "col_nra_m": "سن التقاعد (ذ)",
        "col_nra_f": "سن التقاعد (أ)",
        "col_ee_all": "اشتراك الموظف %",
        "col_er_all": "اشتراك صاحب العمل %",
        "col_scheme": "النظام",
        "col_tier": "المستوى",
        "col_type": "النوع",
        "col_min_yrs": "أدنى سنوات",
        "col_vest_yrs": "سنوات الاستحقاق",
        "col_ee_pct": "اشتراك الموظف%",
        "col_er_pct": "اشتراك صاحح العمل%",
        "col_total_pct": "الإجمالي%",
        "col_ceiling": "السقف",
        "col_ceiling_none": "لا يوجد",
        "col_accrual_yr": "الاستحقاق/سنة",
        "col_flat_rate": "معدل ثابت",
        "col_min_benefit": "أدنى مزايا",
        "col_max_benefit": "أقصى مزايا",
        "col_earnings_measure": "مقياس الأجر",
        "col_valorization": "مؤشرة الاستحقاق",
        "col_accrual_rate_yr": "معدل الاستحقاق/سنة",
        "col_indexation": "المؤشرة",
        "col_indicator": "المؤشر",
        "val_career_average": "متوسط المسيرة المهنية",
        "val_final_salary": "الراتب الأخير",
        "val_revalued_career_avg": "متوسط المسيرة المعدَّل",
        "val_min_wage_base": "الحد الأدنى للأجر",
        "val_wages": "الأجور",
        "val_prices": "الأسعار",
        "val_gdp": "الناتج المحلي الإجمالي",
        "val_investment_returns": "العوائد الاستثمارية",
        "val_discretionary": "تقديري",
        "val_fixed_rate": "معدل ثابت",
        "val_prices_cpi": "الأسعار (مؤشر CPI)",
        "val_mixed": "مختلط (أجور/أسعار)",
        "val_na": "—",
        "ind_gross_rr": "معدل الإحلال الإجمالي (%)",
        "ind_net_rr": "معدل الإحلال الصافي (%)",
        "ind_gross_pl": "مستوى المعاش الإجمالي (% من متوسط الأجر)",
        "ind_net_pl": "مستوى المعاش الصافي (% من متوسط الأجر)",
        "ind_gross_pw": "الثروة التقاعدية الإجمالية (× متوسط الأجر)",
        "ind_net_pw": "الثروة التقاعدية الصافية (× متوسط الأجر)",
        "pag_gross_rr_pct": "معدل الإحلال الإجمالي @ 1×متوسط الأجر (%)",
        "pag_gross_rr_col": "معدل الإحلال الإجمالي (%)",
        "pag_net_rr_col": "معدل الإحلال الصافي (%)",
        "chart_rr_xaxis": "معدل الإحلال (%)",

        # ── Methodology tab ───────────────────────────────────────────────────
        "methodology_header": "📖 المنهجية ومصادر البيانات",
        "methodology_body": """
### منهجية الحساب

تتبع بانوراما المعاشات منهجية **منظمة OECD – 'المعاشات في لمحة'**:

| العنصر | الوصف |
|---|---|
| **سن الدخول** | 20 عاماً |
| **طول المسيرة المهنية** | 40 عاماً |
| **كثافة المساهمة** | 100% من مدة العمل |
| **نمو الأجر الحقيقي** | 2% سنوياً |
| **معدل الخصم** | 2% حقيقي |
| **صافي العائد الحقيقي (DC)** | 3% سنوياً |
| **مؤشرة ما بعد التقاعد** | مؤشر أسعار المستهلك (قيمة حقيقية ثابتة) |
| **الثروة التقاعدية** | القيمة الحالية المرجَّحة بالبقاء ÷ متوسط الأجر |

تُجرى الحسابات عند **ستة مضاعفات للدخل**: 0.5، 0.75، 1.0، 1.5، 2.0، 2.5 × متوسط الأجر الوطني.

---

### المؤشرات

| المؤشر | الصيغة |
|---|---|
| **معدل الإحلال الإجمالي (GRR)** | المعاش السنوي الإجمالي ÷ أجر الفرد قبل التقاعد |
| **معدل الإحلال الصافي (NRR)** | المعاش السنوي الصافي ÷ أجر الفرد قبل التقاعد |
| **مستوى المعاش الإجمالي (GPL)** | المعاش السنوي الإجمالي ÷ متوسط الأجر السنوي |
| **مستوى المعاش الصافي (NPL)** | المعاش السنوي الصافي ÷ متوسط الأجر السنوي |
| **الثروة التقاعدية الإجمالية (GPW)** | القيمة الحالية (تدفق المزايا الإجمالية) ÷ متوسط الأجر |
| **الثروة التقاعدية الصافية (NPW)** | القيمة الحالية (تدفق المزايا الصافية) ÷ متوسط الأجر |

---

### أنواع أنظمة التقاعد المدعومة

| النوع | الوصف |
|---|---|
| `DB` | محدد المزايا: معدل الاستحقاق × سنوات الخدمة × الأجر المرجعي |
| `basic` | معاش أساسي ثابت شامل |
| `targeted` | معاش اجتماعي مُختبَر الدخل (تناقص مبسّط) |
| `minimum` | ضمان الحد الأدنى للمعاش (يُطبَّق كمكمِّل) |
| `points` | نظام نقاط: النقاط = (الأجر ÷ متوسط الأجر) × سنوات الخدمة |
| `NDC` | محدد الاشتراكات الاسمي: حساب اسمي ÷ معامل الأقساط |
| `DC` | محدد الاشتراكات المالي: صندوق متراكم يتحول إلى قسط سنوي |

---

### مصادر البيانات

| الطبقة | المصدر | واجهة API |
|---|---|---|
| **قواعد التقاعد** | ملفات YAML محرَّرة يدوياً | — |
| **متوسط الأجور** | ILOSTAT SDMX API (أساسي)؛ قيم يدوية (احتياطي) | `sdmx.ilo.org/rest` |
| **جداول الوفيات** | بوابة UN WPP (عند التوفر) | `population.un.org/dataportalapi` |
| **السياق الاقتصادي** | واجهة بيانات البنك الدولي | `api.worldbank.org/v2` |

---

### ملاحظات حول التغطية الجغرافية

تحتفظ عدة دول (المملكة العربية السعودية، الإمارات، الكويت، قطر، البحرين، عُمان) **بنظامين متوازيين**:
المواطنون مشمولون بصندوق تقاعد إلزامي؛ العمال الأجانب (الأغلبية في الغالب) يحصلون فقط على
**مكافأة نهاية الخدمة**، وهي مبلغ مقطوع. تُحاكي لوحة المعلومات **نظام المواطنين فقط**.

تحسب الهيئة العمالية في باكستان (EOBI) الاشتراكات على أساس **الحد الأدنى للأجور** لا الأجر الفعلي،
مما يؤدي إلى معدلات إحلال فعلية منخفضة نسبةً إلى متوسط الأجور.

---

### إضافة دولة جديدة

1. انسخ `data/params/_template.yaml` إلى `data/params/<ISO3>.yaml`
2. أكمل جميع الحقول؛ كل معامل يتطلب `source_citation`
3. شغّل `pp validate-params --countries <ISO3>`
4. أعد تحديث لوحة المعلومات — ستظهر الدول الجديدة تلقائياً
""",

        "methodology_pension_calc_body": """
### الغرض

تُقدِّر **حاسبة المعاش الشخصية** قيمة معاش التقاعد لفرد بعينه، مستخدمةً قواعد النظام ذاتها المستخدمة
في نموذج OECD الشامل، لكن مع مدخلات فردية يُدخلها المستخدم بدلاً من مسارات مهنية افتراضية.

---

### المدخلات

| المدخل | الوصف |
|---|---|
| **الدولة** | تحدِّد قواعد النظام ومتوسط الأجر المُطبَّق |
| **نوع العامل** | يختار المسار المنطبق (مواطن، موظف خاص، موظف حكومي…) |
| **الجنس** | يُستخدم لأعمار التقاعد وجداول الوفيات المُتمايزة |
| **العمر الحالي** | يجب أن يبلغ الحد الأدنى لسن التقاعد الاعتيادي |
| **سنوات الخدمة / الاشتراك** | تُتحقَّق من الحد الأدنى المطلوب |
| **الأجر السنوي** | بالعملة المحلية أو كمضاعف للأجر الوطني المتوسط |

---

### أنواع العمال وحالات التغطية

| الحالة | المعنى |
|---|---|
| `covered` مشمول | مشاركة إلزامية؛ يُحسب المعاش كاملاً |
| `excluded` مستثنى | غير مشمول بالنظام الإلزامي (كالعمالة الوافدة في دول الخليج)؛ المعاش = صفر |
| `unknown` غير محدد | الوضع غير واضح؛ النتائج استرشادية فقط |

---

### شرط الأهلية

يستحق العامل المعاش إذا تحقَّقت جميع الشروط التالية:
- العمر الحالي ≥ سن التقاعد الاعتيادي للجنس المعني
- سنوات الخدمة ≥ الحد الأدنى المطلوب (إن وُجد)
- حالة التغطية ليست `excluded`

---

### حساب المزايا

| نوع النظام | الصيغة |
|---|---|
| `DB` محدد المزايا | `معدل الاستحقاق × min(سنوات الخدمة، الحد الأقصى) × الأجر المرجعي` |
| `basic` أساسي | مبلغ ثابت (مُحدَّد بالعملة أو كنسبة من متوسط الأجر) |
| `targeted` مُختبَر الدخل | `الحد الأقصى − معدل التناقص × (الأجر − العتبة)` |
| `minimum` حد أدنى | يُطبَّق كمكمِّل إذا قلَّ المجموع عن الحد الأدنى |
| `points` نقاط | `(الأجر ÷ متوسط الأجر) × نقاط/سنة × السنوات × قيمة النقطة` |
| `NDC` اسمي | `رصيد الحساب الاسمي ÷ معامل الأقساط` |
| `DC` مالي | `الصندوق المتراكم ÷ معامل الأقساط` |

---

### مصادر البيانات

| البيانات | المصدر |
|---|---|
| قواعد النظام | ملفات YAML محرَّرة يدوياً |
| متوسط الأجر الوطني | ILOSTAT SDMX API (أساسي)؛ قيم يدوية (احتياطي) |
| جداول الوفيات | بوابة UN WPP |
| قواعد الضريبة | ملفات YAML محرَّرة يدوياً |
""",

        "methodology_rc_body": """
### الغرض

تُقدِّر **حاسبة تكلفة التقاعد** المبلغ الذي يحتاجه الشخص لتمويل فترة تقاعده، شاملاً نفقات المعيشة
والإنفاق الصحي من الجيب الخاص، بالعملة المحلية وبالدولار بتعادل القوة الشرائية.
تُستقى جميع البيانات من واجهات برمجية مفتوحة مع الاستشهاد بكل رقم.

---

### الخطوة 1 — أفق التقاعد

يُقدَّر عدد سنوات التقاعد من **أمل الحياة المتبقية عند سن التقاعد** وفق سلسلة أولويات:

| الأولوية | المصدر | الطريقة |
|---|---|---|
| 1 (أساسي) | بوابة UN WPP — المؤشر 75 | أمل الحياة المتبقي عند السن المحددة، آخر إسقاط 2020–2030 |
| 2 (بديل) | WHO GHO — `WHOSIS_000007` | HALE عند سن 60 كبديل عند غياب بيانات UN WPP |
| 3 (غير كافٍ) | — | لا بيانات متاحة؛ لا يمكن حساب التكلفة مدى الحياة |

---

### الخطوة 2 — تقسيم HALE (سنوات صحية / غير صحية)

عند تفعيل **استخدام تقسيم HALE**، يُقسَّم أفق التقاعد إلى:
- **سنوات صحية** = HALE عند سن التقاعد (من WHO GHO)
- **سنوات غير صحية** = إجمالي الأفق − السنوات الصحية

تستقطب السنوات غير الصحية إنفاقاً صحياً أعلى (انظر الخطوة 4).

---

### الخطوة 3 — هدف الإنفاق الاستهلاكي السنوي

| الطبقة | المصدر | متى تُستخدم |
|---|---|---|
| **الطبقة 1** | خط الفقر الوطني × مضاعف السيناريو | عند توفر خط فقر وطني محدد |
| **الطبقة 3** | نصيب الفرد من HFCE × مضاعف السيناريو | الافتراضي لجميع الدول |

**مضاعفات السيناريو (على نصيب الفرد من HFCE):**

| السيناريو | المضاعف | المبرر |
|---|---|---|
| أساسي | 0.55 × HFCE/فرد | إنفاق على مستوى الكفاف |
| متوسط | 0.75 × HFCE/فرد | راحة معقولة؛ الافتراضي |
| مريح | 1.00 × HFCE/فرد | الحفاظ على مستوى المعيشة قبل التقاعد |

---

### الخطوة 4 — الإنفاق الصحي من الجيب سنوياً

**الأساس** = (`SH.XPD.OOPC.CH.ZS` ÷ 100) × `SH.XPD.CHEX.PC.CD` × معامل PPP

مع تقسيم HALE:
```
الإنفاق السنوي = (سنوات صحية × الأساس + سنوات غير صحية × الأساس × معامل الارتفاع العمري)
                 ÷ إجمالي الأفق
```

**معامل الارتفاع العمري** (افتراضي 1.5×) يعكس ارتفاع الاستخدام الصحي في سنوات التدهور الصحي.

---

### الخطوة 5 — القيمة الحالية مدى الحياة

إجمالي التكلفة السنوية = هدف الاستهلاك + الإنفاق الصحي (إذا فُعِّل).

**القيمة الحالية للتكلفة مدى الحياة:**

```
PV = Σ_{t=1}^{H}  [التكلفة_السنوية × (1 + g)^(t−1)] / (1 + r)^t
```

حيث: `H` = أفق التقاعد | `g` = معدل التضخم | `r` = معدل الخصم الاسمي

**الدخل الشهري المطلوب** = PV ÷ (H × 12)

---

### مصادر البيانات

| المؤشر | رمز WDI | الاستخدام |
|---|---|---|
| نصيب الفرد من HFCE (دولار 2015) | `NE.CON.PRVT.PC.KD` | أساس الاستهلاك (الطبقة 3) |
| الإنفاق الصحي الجاري للفرد | `SH.XPD.CHEX.PC.CD` | أساس الإنفاق الصحي |
| نسبة الإنفاق من الجيب | `SH.XPD.OOPC.CH.ZS` | أساس الإنفاق الصحي |
| معامل PPP | `PA.NUS.PPP` | تحويل العملة المحلية |
| نصيب الفرد من GDP | `NY.GDP.PCAP.CD` | نسبة المعيار |
| HALE عند سن 60 | WHO GHO `WHOSIS_000007` | تقسيم السنوات الصحية |
| أمل الحياة المتبقي | UN WPP المؤشر 75 | أفق التقاعد |

---

### القيود والتحفظات

- التكاليف بالعملة المحلية **بأسعار اليوم**؛ تُطبَّق التضخم والخصم في حساب القيمة الحالية.
- بيانات الإنفاق الصحي من WDI تمثل **متوسط السكان** لا المتقاعدين تحديداً.
- النتائج **تقديرية** للمقارنة التوضيحية فقط، وليست نصيحة تخطيط مالي.
""",
    },
}
