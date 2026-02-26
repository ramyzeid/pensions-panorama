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
        "subtab_modeling": "📊 Modeling Results",
        "subtab_system_overview": "📘 System Overview",
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
        "glossary_indicators_title": "📊 Pension Indicators",
        "glossary_indicators_body": (
            "| Term | Abbreviation | Definition |\n"
            "|---|---|---|\n"
            "| **Gross Replacement Rate** | GRR | Gross annual pension ÷ individual gross pre-retirement earnings. Measures how much of working income the pension replaces before tax. |\n"
            "| **Net Replacement Rate** | NRR | Net annual pension ÷ individual net pre-retirement earnings (after worker social contributions and income tax). The more meaningful measure of living-standard maintenance. |\n"
            "| **Gross Pension Level** | GPL | Gross annual pension ÷ national average earnings. Shows the pension's value relative to economy-wide wages, enabling cross-country comparison independent of individual earnings. |\n"
            "| **Net Pension Level** | NPL | Net annual pension ÷ average net earnings. Net-of-tax version of GPL. |\n"
            "| **Gross Pension Wealth** | GPW | Present value of the entire gross benefit stream, discounted and survival-weighted, divided by the average wage. Measures the stock of pension wealth rather than annual flow. |\n"
            "| **Net Pension Wealth** | NPW | Same as GPW but using the net benefit stream. |\n"
            "| **Accrual Rate** | — | The share of reference earnings credited as pension per year of service in a DB scheme (e.g. 2% means 40 years × 2% = 80% replacement). |\n"
            "| **Normal Retirement Age** | NRA | The age at which a worker becomes entitled to a full pension benefit without reduction. May differ by sex. |\n"
            "| **Effective Retirement Age** | ERA | The actual average age at which workers exit the labour force, which often differs from the statutory NRA due to early retirement provisions. |\n"
            "| **Contribution Rate** | — | The percentage of wages paid into the pension system, typically split between employer and employee. |\n"
            "| **Replacement Wage** | — | The wage base used to calculate DB benefits — may be final salary, career-average earnings, or best N years. |\n"
            "| **Vesting Period** | — | Minimum service / contribution years required before a worker is entitled to any pension benefit. |"
        ),
        "glossary_schemes_title": "🏛️ Scheme Types",
        "glossary_schemes_body": (
            "| Type | Full Name | How it works |\n"
            "|---|---|---|\n"
            "| **DB** | Defined Benefit | Pension = accrual rate × service years × reference wage. The sponsor bears investment and longevity risk. |\n"
            "| **DC** | Defined Contribution | Worker and/or employer accumulate a fund; at retirement the fund is converted to an annuity or drawn down. Worker bears investment risk. |\n"
            "| **NDC** | Non-Financial (Notional) Defined Contribution | Contributions earn a notional return (usually GDP or wage growth) in individual accounts, but the system remains pay-as-you-go funded. Combines DC-like benefit link with PAYG financing. |\n"
            "| **Points** | Points System | Each year a worker earns points = wage ÷ average wage. Total points × point value at retirement = pension. Used in France, Germany. |\n"
            "| **Basic / Flat-rate** | — | A uniform pension paid to all qualifying residents or contributors regardless of earnings history. Provides a basic floor. |\n"
            "| **Targeted / Means-tested** | — | Benefit phases out as income rises; directed at low-income retirees. |\n"
            "| **Minimum pension guarantee** | — | A floor applied as a top-up: if computed pension < minimum, the state pays the difference. |\n"
            "| **EOSB** | End-of-Service Benefit | A lump-sum gratuity paid by the employer at the end of employment, typically proportional to final salary × service years. Common for expatriate workers in GCC countries as a substitute for pension coverage. |\n"
            "| **PAYG** | Pay-As-You-Go | Financing mechanism: current contributions pay current retirees' benefits. No pre-funding of future liabilities. |\n"
            "| **Funded** | — | Assets are accumulated in advance in a fund (individual or collective) to pay future benefits. |"
        ),
        "glossary_health_title": "❤️ Life Expectancy & Health",
        "glossary_health_body": (
            "| Term | Abbreviation | Definition |\n"
            "|---|---|---|\n"
            "| **Life Expectancy at birth** | LE₀ | Expected number of years a newborn would live under current mortality conditions. |\n"
            "| **Life Expectancy at age x** | LE(x) or e(x) | Expected additional years of life for a person who has already reached age x. Used to determine the retirement horizon. |\n"
            "| **Healthy Adjusted Life Expectancy** | HALE | Years of life expected to be lived in \"full health\" (free from significant disability or disease). Derived by subtracting years lived with disability from total LE. |\n"
            "| **HALE at 60** | — | WHO GHO indicator `WHOSIS_000007`. HALE remaining at age 60, used to split the retirement horizon into healthy and unhealthy years. |\n"
            "| **Age-specific LE** | — | UN WPP indicator 75. Remaining LE at an exact age group (60, 65, etc.), more precise than birth-based LE for retirement planning. |\n"
            "| **Longevity risk** | — | The risk that retirees outlive their savings. Managed through annuities, longevity bonds, or PAYG elements. |\n"
            "| **Survival-weighted PV** | — | Present value of a benefit stream where each future payment is discounted both for time (discount rate) and for the probability of still being alive (survival probability). Used in pension wealth calculations. |"
        ),
        "glossary_economic_title": "💹 Economic & Data Indicators",
        "glossary_economic_body": (
            "| Term / Code | Full Name | Definition |\n"
            "|---|---|---|\n"
            "| **HFCE** · `NE.CON.PRVT.PC.KD` | Household Final Consumption Expenditure per capita | Total spending by households on goods and services, per person, in constant 2015 USD. Used as the Tier 3 consumption baseline. |\n"
            "| **CHE** · `SH.XPD.CHEX.PC.CD` | Current Health Expenditure per capita | Total health spending (public + private) per person in current USD. |\n"
            "| **OOP** · `SH.XPD.OOPC.CH.ZS` | Out-of-Pocket health spending as % of CHE | Share of total health spending paid directly by households, not covered by insurance. |\n"
            "| **PPP factor** · `PA.NUS.PPP` | Purchasing Power Parity conversion factor | Local currency units per international dollar. Converts local currency to a comparable real value across countries. |\n"
            "| **GDP per capita** · `NY.GDP.PCAP.CD` | Gross Domestic Product per capita | Total economic output per person in current USD. Used as a wage proxy and benchmark ratio denominator. |\n"
            "| **Average Wage** · AW | National Average Earnings | Economy-wide average annual gross wage; the denominator for pension levels, wealth, and replacement rates. Sourced from ILOSTAT or seeded manually. |\n"
            "| **WDI** | World Development Indicators | World Bank's flagship database of development data, covering 1,600+ indicators for 200+ countries. API: `api.worldbank.org/v2`. |\n"
            "| **ILO / ILOSTAT** | International Labour Organization statistics | Global labour statistics database. Used for average wage data via SDMX API at `sdmx.ilo.org/rest`. |\n"
            "| **WHO GHO** | WHO Global Health Observatory | WHO's open data repository for health-related statistics. OData API at `ghoapi.azureedge.net/api`. |\n"
            "| **UN WPP** | UN World Population Prospects | UN Population Division's biennial demographic estimates and projections. API at `population.un.org/dataportalapi`. |\n"
            "| **PIP** | World Bank Poverty and Inequality Platform | Harmonised household survey data for poverty and inequality. API returns empty for most countries in scope — not used in this dashboard. |"
        ),
        "glossary_rc_title": "🔢 Retirement Cost Calculator Terms",
        "glossary_rc_body": (
            "| Term | Definition |\n"
            "|---|---|\n"
            "| **Retirement horizon** | Estimated number of years spent in retirement = remaining life expectancy at the retirement age. |\n"
            "| **Healthy years** | Portion of the retirement horizon expected to be spent in good health (from HALE split). |\n"
            "| **Unhealthy years** | Retirement years spent with significant disability or chronic illness; associated with higher health costs. |\n"
            "| **Consumption tier** | The data source used for the living cost baseline. Tier 1 = national poverty line; Tier 3 = HFCE per capita. Tier 2 (PIP) is not used. |\n"
            "| **Scenario multiplier** | Factor applied to the consumption baseline to reflect lifestyle: Basic (0.55×), Moderate (0.75×), Comfortable (1.0×) of HFCE/capita. |\n"
            "| **Age uplift factor** | Multiplier applied to baseline health OOP spending during unhealthy years (default 1.5×), reflecting higher healthcare utilisation. |\n"
            "| **Discount rate** | Rate used to reduce future costs to present-day value. A higher rate means future costs matter less today. |\n"
            "| **Inflation rate** | Rate at which costs grow each year, increasing the nominal amount needed in future years. |\n"
            "| **Lifetime present value (PV)** | Sum of all discounted annual retirement costs over the full horizon — the lump sum needed at retirement date. |\n"
            "| **Required monthly income** | Lifetime PV ÷ (horizon years × 12). The steady monthly draw needed to fund retirement, in today's money. |\n"
            "| **PPP-USD equivalent** | Annual cost converted to international dollars using the PPP factor, allowing comparison across countries. |\n"
            "| **Horizon method** | Label indicating the data source used for life expectancy: `UN_WPP_exact` (primary), `WHO_GHO_LE60_proxy` (fallback). |"
        ),
        "glossary_coverage_title": "🌍 Country Coverage & System Notes",
        "glossary_coverage_body": (
            "| Topic | Note |\n"
            "|---|---|\n"
            "| **GCC dual-track systems** | Saudi Arabia, UAE, Kuwait, Qatar, Bahrain, and Oman operate parallel systems: mandatory pension funds for national citizens; End-of-Service Benefits (EOSB) for expatriates. This dashboard models the **national citizen scheme only**. |\n"
            "| **Pakistan EOBI** | The Employees' Old-Age Benefits Institution calculates contributions on the **minimum wage**, not the actual wage. This produces low effective replacement rates relative to average earnings for higher earners. |\n"
            "| **Expatriate coverage** | In most GCC countries, expatriate workers (often the majority of the workforce) are explicitly excluded from the mandatory pension system. Their worker type is marked `excluded` and their modelled benefit is zero. |\n"
            "| **Civil servant schemes** | Several countries maintain separate, more generous pension schemes for civil servants. Where data is available these are modelled as distinct worker types. |\n"
            "| **Multi-pillar systems** | Most modern systems combine a PAYG DB pillar (first pillar) with a funded DC pillar (second pillar) and voluntary savings (third pillar). All pillars present in the country YAML are modelled simultaneously. |"
        ),
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
        "subtab_modeling": "📊 نتائج النمذجة",
        "subtab_system_overview": "📘 نظرة عامة على النظام",
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
        "glossary_indicators_title": "📊 مؤشرات التقاعد",
        "glossary_indicators_body": (
            "| المصطلح | الاختصار | التعريف |\n"
            "|---|---|---|\n"
            "| **معدل الإحلال الإجمالي** | GRR | المعاش السنوي الإجمالي ÷ الدخل الإجمالي للفرد قبل التقاعد. يقيس مقدار دخل العمل الذي يعوّضه المعاش قبل الضريبة. |\n"
            "| **معدل الإحلال الصافي** | NRR | المعاش السنوي الصافي ÷ الدخل الصافي للفرد قبل التقاعد (بعد اشتراكات الضمان الاجتماعي وضريبة الدخل). المقياس الأكثر دلالةً على الحفاظ على مستوى المعيشة. |\n"
            "| **مستوى المعاش الإجمالي** | GPL | المعاش السنوي الإجمالي ÷ متوسط الأجور الوطنية. يُظهر قيمة المعاش نسبةً إلى الأجور على مستوى الاقتصاد، مما يتيح المقارنة بين الدول. |\n"
            "| **مستوى المعاش الصافي** | NPL | المعاش السنوي الصافي ÷ متوسط الأجور الصافية. نسخة GPL بعد خصم الضريبة. |\n"
            "| **ثروة المعاش الإجمالية** | GPW | القيمة الحالية لمجمل تدفقات الاستحقاق الإجمالية، مخصومةً ومرجَّحةً بمعدلات البقاء على قيد الحياة، مقسومةً على متوسط الأجر. |\n"
            "| **ثروة المعاش الصافية** | NPW | مماثلة لـ GPW لكن باستخدام تدفقات الاستحقاق الصافية. |\n"
            "| **معدل الاستحقاق** | — | حصة الأجر المرجعي التي تُحتسب معاشاً عن كل سنة خدمة في نظام DB. |\n"
            "| **سن التقاعد الاعتيادي** | NRA | السن التي يصبح عندها العامل مستحقاً لمعاش تقاعد كامل دون أي خفض. قد يختلف بحسب الجنس. |\n"
            "| **سن التقاعد الفعلي** | ERA | متوسط السن الفعلي الذي يغادر عنده العمال سوق العمل. |\n"
            "| **معدل الاشتراك** | — | نسبة الأجور المدفوعة في نظام التقاعد، مقسَّمةً بين صاحب العمل والموظف. |\n"
            "| **الأجر الاستبدالي** | — | قاعدة الأجر المستخدمة لاحتساب مزايا DB — قد تكون الراتب الأخير أو متوسط المسار الوظيفي أو أفضل N سنة. |\n"
            "| **فترة الاستحقاق** | — | الحد الأدنى من سنوات الخدمة المطلوبة قبل أن يصبح العامل مستحقاً لأي مزايا تقاعدية. |"
        ),
        "glossary_schemes_title": "🏛️ أنواع الأنظمة التقاعدية",
        "glossary_schemes_body": (
            "| النوع | الاسم الكامل | آلية العمل |\n"
            "|---|---|---|\n"
            "| **DB** | المزايا المحددة | المعاش = معدل الاستحقاق × سنوات الخدمة × الأجر المرجعي. يتحمل الجهة الراعية مخاطر الاستثمار والعمر. |\n"
            "| **DC** | الاشتراكات المحددة | يتراكم العامل و/أو صاحب العمل صندوقاً؛ عند التقاعد يُحوَّل الصندوق إلى راتب سنوي أو يُسحب تدريجياً. يتحمل العامل مخاطر الاستثمار. |\n"
            "| **NDC** | الاشتراكات المحددة الافتراضية (غير المالية) | تكسب الاشتراكات عائداً افتراضياً في حسابات فردية، غير أن النظام يظل ممولاً بأسلوب PAYG. |\n"
            "| **النقاط** | نظام النقاط | يكسب العامل سنوياً نقاطاً = الأجر ÷ متوسط الأجر. إجمالي النقاط × قيمة النقطة عند التقاعد = المعاش. |\n"
            "| **الأساسي / الموحد** | — | معاش موحد يُدفع لجميع المقيمين أو المشتركين المستوفين للشروط بصرف النظر عن تاريخ الأجر. |\n"
            "| **المستهدف / الخاضع لاختبار الدخل** | — | تتناقص المزايا مع ارتفاع الدخل؛ موجَّه للمتقاعدين من ذوي الدخل المنخفض. |\n"
            "| **ضمان الحد الأدنى للمعاش** | — | حد أدنى يُطبَّق كمكمّل: إذا كان المعاش المحتسب أقل من الحد الأدنى، تدفع الدولة الفرق. |\n"
            "| **EOSB** | مكافأة نهاية الخدمة | مبلغ إجمالي يدفعه صاحب العمل عند انتهاء الخدمة. شائعة للعمال الوافدين في دول GCC. |\n"
            "| **PAYG** | الدفع الجاري | تموّل الاشتراكات الحالية مزايا المتقاعدين الحاليين. لا يوجد تمويل مسبق للالتزامات المستقبلية. |\n"
            "| **ممول** | — | تُجمَّع الأصول مسبقاً في صندوق لدفع المزايا المستقبلية. |"
        ),
        "glossary_health_title": "❤️ العمر المتوقع والصحة",
        "glossary_health_body": (
            "| المصطلح | الاختصار | التعريف |\n"
            "|---|---|---|\n"
            "| **العمر المتوقع عند الولادة** | LE₀ | عدد السنوات المتوقعة التي سيعيشها المولود في ظل ظروف الوفيات الحالية. |\n"
            "| **العمر المتوقع عند السن x** | LE(x) | السنوات الإضافية المتوقعة في الحياة لمن بلغ بالفعل السن x. يُستخدم لتحديد أفق التقاعد. |\n"
            "| **العمر المتوقع المعدَّل بالصحة** | HALE | سنوات الحياة المتوقع قضاؤها بصحة كاملة. يُحتسب بطرح سنوات العيش مع الإعاقة من إجمالي العمر المتوقع. |\n"
            "| **HALE عند سن 60** | — | مؤشر WHO GHO ذو الرمز `WHOSIS_000007`. العمر المتوقع الصحي المتبقي عند سن 60، يُستخدم لتقسيم أفق التقاعد إلى سنوات صحية وأخرى غير صحية. |\n"
            "| **العمر المتوقع حسب الفئة العمرية** | — | مؤشر UN WPP رقم 75. العمر المتوقع المتبقي عند فئة عمرية محددة (60، 65، وما إلى ذلك). |\n"
            "| **مخاطر طول العمر** | — | مخاطر أن يعيش المتقاعدون أطول من مدخراتهم. تُدار من خلال الدخل السنوي المضمون أو عناصر PAYG. |\n"
            "| **القيمة الحالية المرجَّحة بالبقاء** | — | القيمة الحالية التي يُخصم فيها كل دفع مستقبلي بحسب الزمن واحتمالية البقاء على قيد الحياة. تُستخدم في احتساب ثروة المعاش. |"
        ),
        "glossary_economic_title": "💹 المؤشرات الاقتصادية ومصادر البيانات",
        "glossary_economic_body": (
            "| المصطلح / الرمز | الاسم الكامل | التعريف |\n"
            "|---|---|---|\n"
            "| **HFCE** · `NE.CON.PRVT.PC.KD` | الإنفاق الاستهلاكي النهائي للأسر المعيشية للفرد | إجمالي إنفاق الأسر على السلع والخدمات، للفرد، بالدولار الأمريكي الثابت لعام 2015. |\n"
            "| **CHE** · `SH.XPD.CHEX.PC.CD` | الإنفاق الصحي الجاري للفرد | إجمالي الإنفاق الصحي للفرد بالدولار الأمريكي الجاري. |\n"
            "| **OOP** · `SH.XPD.OOPC.CH.ZS` | الإنفاق الصحي من الجيب كنسبة من CHE | حصة إجمالي الإنفاق الصحي التي تدفعها الأسر مباشرةً. |\n"
            "| **معامل PPP** · `PA.NUS.PPP` | معامل تحويل تعادل القوة الشرائية | وحدات العملة المحلية مقابل الدولار الدولي. |\n"
            "| **الناتج المحلي الإجمالي للفرد** · `NY.GDP.PCAP.CD` | الناتج المحلي الإجمالي للفرد | إجمالي الناتج الاقتصادي للفرد بالدولار الأمريكي الجاري. |\n"
            "| **متوسط الأجر** · AW | متوسط الأجر الوطني | متوسط الأجر السنوي الإجمالي على مستوى الاقتصاد؛ المقام المستخدم في مستويات المعاش ومعدلات الإحلال. |\n"
            "| **WDI** | مؤشرات التنمية العالمية | قاعدة البيانات الرئيسية للبنك الدولي. الواجهة البرمجية: `api.worldbank.org/v2`. |\n"
            "| **ILO / ILOSTAT** | إحصاءات منظمة العمل الدولية | إحصاءات العمل العالمية. الواجهة البرمجية: `sdmx.ilo.org/rest`. |\n"
            "| **WHO GHO** | المرصد الصحي العالمي لمنظمة الصحة العالمية | البيانات المفتوحة لمنظمة الصحة العالمية للإحصاءات الصحية. الواجهة البرمجية: `ghoapi.azureedge.net/api`. |\n"
            "| **UN WPP** | توقعات الأمم المتحدة للسكان في العالم | التقديرات الديموغرافية والإسقاطات الأممية. الواجهة البرمجية: `population.un.org/dataportalapi`. |"
        ),
        "glossary_rc_title": "🔢 مصطلحات حاسبة تكلفة التقاعد",
        "glossary_rc_body": (
            "| المصطلح | التعريف |\n"
            "|---|---|\n"
            "| **أفق التقاعد** | السنوات التقديرية التي تُقضى في التقاعد = العمر المتوقع المتبقي عند سن التقاعد. |\n"
            "| **السنوات الصحية** | الجزء من أفق التقاعد المتوقع قضاؤه بصحة جيدة (مستمَد من تقسيم HALE). |\n"
            "| **السنوات غير الصحية** | سنوات التقاعد المصحوبة بإعاقة كبيرة أو مرض مزمن؛ تكاليف صحية أعلى. |\n"
            "| **مستوى الاستهلاك** | مصدر البيانات لخط الأساس لتكلفة المعيشة. المستوى الأول = خط الفقر؛ المستوى الثالث = HFCE للفرد. |\n"
            "| **مضاعف السيناريو** | المعامل المطبَّق على خط أساس الاستهلاك: أساسي (0.55×)، معتدل (0.75×)، مريح (1.0×) من HFCE/للفرد. |\n"
            "| **معامل الرفع العمري** | المضاعف لتكاليف OOP الصحية خلال السنوات غير الصحية (الافتراضي 1.5×). |\n"
            "| **معدل الخصم** | المعدل المستخدم لاختزال التكاليف المستقبلية إلى قيمتها الحالية. |\n"
            "| **معدل التضخم** | المعدل الذي ترتفع به التكاليف سنوياً. |\n"
            "| **القيمة الحالية الإجمالية مدى الحياة (PV)** | مجموع جميع تكاليف التقاعد السنوية المخصومة — المبلغ الإجمالي المطلوب في تاريخ التقاعد. |"
        ),
        "glossary_coverage_title": "🌍 ملاحظات التغطية والأنظمة",
        "glossary_coverage_body": (
            "| الموضوع | ملاحظة |\n"
            "|---|---|\n"
            "| **أنظمة دول الخليج المزدوجة** | تعمل السعودية والإمارات والكويت وقطر والبحرين وعُمان بأنظمة موازية: صناديق معاشات إلزامية للمواطنين؛ ومكافأة نهاية الخدمة للعمالة الوافدة. تُنمذج لوحة المعلومات **نظام المواطنين فقط**. |\n"
            "| **مؤسسة EOBI الباكستانية** | تحتسب مؤسسة مزايا الشيخوخة للموظفين الاشتراكات على أساس **الحد الأدنى للأجور**، لا الأجر الفعلي. مما ينتج عنه معدلات إحلال فعلية منخفضة بالنسبة لمتوسط الأجر لأصحاب الدخل المرتفع. |\n"
            "| **تغطية العمالة الوافدة** | في معظم دول الخليج، يُستثنى العمال الوافدون (الغالبية في أغلب الأحيان) صراحةً من نظام المعاشات الإلزامي. يُصنَّف نوع عملهم بـ `excluded` وتكون مزاياهم المنمذجة صفراً. |\n"
            "| **أنظمة موظفي الحكومة** | تحتفظ عدة دول بأنظمة معاشات أكثر سخاءً لموظفي الحكومة. تُنمذَج كأنواع عمال مستقلة حيثما توفرت البيانات. |\n"
            "| **أنظمة متعددة الأعمدة** | تجمع معظم الأنظمة الحديثة بين عمود PAYG-DB (الأول) وعمود DC ممول (الثاني) ومدخرات طوعية (الثالث). تُنمذَج جميع الأعمدة الواردة في YAML المعني في آنٍ واحد. |"
        ),
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

    # =========================================================================
    # FRENCH
    # =========================================================================
    "fr": {
        "app_title": "Base de données des retraites",
        "app_subtitle": "Ensemble de données comparatives sur les retraites",
        "reference_year": "Année de référence",
        "modeled_sex": "Sexe modélisé",
        "opt_male": "homme",
        "opt_female": "femme",
        "opt_all": "tous (moyenne H+F)",
        "overview_multiple_caption": "Multiple de salaire pour la vue d'ensemble",
        "earnings_multiple_label": "Multiple de salaire (×SM)",
        "footer": "v0.1 · données : Banque mondiale, UN WPP, ILOSTAT",
        "language_label": "🌐 Langue",
        "loading_spinner": "Chargement des données de retraite pour tous les pays…",
        "tab_panorama": "🏠 Base de données",
        "tab_country": "🌍 Profil pays",
        "tab_deep_profile": "📘 Profil pays approfondi",
        "subtab_modeling": "📊 Résultats de modélisation",
        "subtab_system_overview": "📘 Vue d'ensemble du système",
        "tab_compare": "📊 Comparer",
        "tab_methodology": "📖 Méthodologie",
        "tab_pag": "📋 Tableaux PAG",
        "tab_calculator": "🧮 Calculateur de retraite",
        "tab_retirement_cost": "💰 Coût de la retraite",
        "methodology_section_oecd": "📐 Modèle de retraite OECD",
        "methodology_section_pension_calc": "🧮 Calculateur de retraite",
        "methodology_section_rc": "💰 Calculateur du coût de la retraite",
        "tab_glossary": "📖 Glossaire",
        "glossary_intro": "Définitions de chaque indicateur, type de régime et terme utilisé dans ce tableau de bord.",
        "glossary_indicators_title": "📊 Indicateurs de retraite",
        "glossary_indicators_body": (
            "| Terme | Abrév. | Définition |\n"
            "|---|---|---|\n"
            "| **Taux de remplacement brut** | GRR | Pension annuelle brute ÷ revenus bruts individuels avant la retraite. Mesure dans quelle proportion la pension remplace les revenus d'activité avant impôt. |\n"
            "| **Taux de remplacement net** | NRR | Pension annuelle nette ÷ revenus nets individuels avant la retraite (après cotisations sociales et impôt sur le revenu). La mesure la plus pertinente pour évaluer le maintien du niveau de vie. |\n"
            "| **Niveau de pension brut** | GPL | Pension annuelle brute ÷ salaire moyen national. Montre la valeur de la pension par rapport aux salaires de l'ensemble de l'économie, permettant des comparaisons entre pays. |\n"
            "| **Niveau de pension net** | NPL | Pension annuelle nette ÷ salaire net moyen. Version après impôt du GPL. |\n"
            "| **Patrimoine retraite brut** | GPW | Valeur actuelle de l'ensemble des flux de prestations brutes, actualisée et pondérée par les probabilités de survie, divisée par le salaire moyen. |\n"
            "| **Patrimoine retraite net** | NPW | Identique au GPW mais en utilisant les flux de prestations nettes. |\n"
            "| **Taux d'accumulation** | — | Part du salaire de référence créditée comme pension pour chaque année de service dans un régime DB. |\n"
            "| **Âge normal de la retraite** | NRA | Âge auquel un travailleur devient éligible à une pension complète sans réduction. Peut varier selon le sexe. |\n"
            "| **Âge effectif de la retraite** | ERA | Âge moyen réel auquel les travailleurs quittent le marché du travail. |\n"
            "| **Taux de cotisation** | — | Pourcentage des salaires versé au régime de retraite, généralement partagé entre employeur et employé. |\n"
            "| **Salaire de référence** | — | Base salariale utilisée pour calculer les prestations DB — peut être le dernier salaire, la moyenne de carrière ou les meilleures N années. |\n"
            "| **Période d'acquisition** | — | Nombre minimal d'années de service ou de cotisation requises avant qu'un travailleur soit éligible à toute prestation de retraite. |"
        ),
        "glossary_schemes_title": "🏛️ Types de régimes",
        "glossary_schemes_body": (
            "| Type | Nom complet | Fonctionnement |\n"
            "|---|---|---|\n"
            "| **DB** | Prestations définies | Pension = taux d'accumulation × années de service × salaire de référence. Le promoteur supporte les risques d'investissement et de longévité. |\n"
            "| **DC** | Cotisations définies | Le travailleur et/ou l'employeur accumulent un capital ; à la retraite, le capital est converti en rente ou retiré progressivement. Le travailleur supporte le risque d'investissement. |\n"
            "| **NDC** | Cotisations définies notionnelles (non financières) | Les cotisations génèrent un rendement notionnel (généralement lié à la croissance du PIB ou des salaires) sur des comptes individuels, mais le régime reste financé en répartition. |\n"
            "| **Points** | Régime par points | Chaque année, le travailleur accumule des points = salaire ÷ salaire moyen. Total des points × valeur du point à la retraite = pension. Utilisé en France et en Allemagne. |\n"
            "| **De base / Forfaitaire** | — | Pension uniforme versée à tous les résidents ou cotisants qualifiés, indépendamment des revenus antérieurs. |\n"
            "| **Ciblée / Sous condition de ressources** | — | Les prestations diminuent à mesure que les revenus augmentent ; destinée aux retraités à faibles revenus. |\n"
            "| **Garantie de pension minimale** | — | Un plancher appliqué en complément : si la pension calculée est inférieure au minimum, l'État verse la différence. |\n"
            "| **EOSB** | Indemnité de fin de service | Somme forfaitaire versée par l'employeur à la fin du contrat de travail. Courante pour les travailleurs expatriés dans les pays du CCG. |\n"
            "| **PAYG** | Répartition | Les cotisations actuelles financent les prestations des retraités actuels. Aucune capitalisation préalable des engagements futurs. |\n"
            "| **Capitalisé** | — | Les actifs sont accumulés à l'avance dans un fonds (individuel ou collectif) pour payer les prestations futures. |"
        ),
        "glossary_health_title": "❤️ Espérance de vie et santé",
        "glossary_health_body": (
            "| Terme | Abrév. | Définition |\n"
            "|---|---|---|\n"
            "| **Espérance de vie à la naissance** | LE₀ | Nombre d'années qu'un nouveau-né est censé vivre dans les conditions de mortalité actuelles. |\n"
            "| **Espérance de vie à l'âge x** | LE(x) ou e(x) | Années de vie supplémentaires attendues pour une personne ayant déjà atteint l'âge x. Utilisée pour estimer l'horizon de retraite. |\n"
            "| **Espérance de vie en bonne santé** | HALE | Années de vie en « pleine santé » (sans handicap ni maladie significative). Calculée en soustrayant les années vécues avec incapacité de l'espérance de vie totale. |\n"
            "| **HALE à 60 ans** | — | Indicateur WHO GHO `WHOSIS_000007`. HALE résiduelle à 60 ans, utilisée pour répartir l'horizon de retraite entre années en bonne santé et années en mauvaise santé. |\n"
            "| **Espérance de vie par groupe d'âge** | — | Indicateur UN WPP 75. Espérance de vie résiduelle à un groupe d'âge précis (60, 65, etc.). |\n"
            "| **Risque de longévité** | — | Risque que les retraités vivent plus longtemps que leurs économies. Géré via des rentes garanties, des obligations de longévité ou des éléments PAYG. |\n"
            "| **Valeur actuelle pondérée par la survie** | — | Valeur actuelle d'un flux de prestations où chaque paiement futur est actualisé à la fois pour le temps et la probabilité d'être encore en vie. Utilisée dans le calcul du patrimoine retraite. |"
        ),
        "glossary_economic_title": "💹 Indicateurs économiques et sources de données",
        "glossary_economic_body": (
            "| Terme / Code | Nom complet | Définition |\n"
            "|---|---|---|\n"
            "| **HFCE** · `NE.CON.PRVT.PC.KD` | Dépenses de consommation finale des ménages par habitant | Dépenses totales des ménages en biens et services, par personne, en USD constants 2015. |\n"
            "| **CHE** · `SH.XPD.CHEX.PC.CD` | Dépenses de santé courantes par habitant | Dépenses de santé totales (publiques + privées) par personne en USD courants. |\n"
            "| **OOP** · `SH.XPD.OOPC.CH.ZS` | Dépenses de santé à la charge des patients en % du CHE | Part des dépenses totales de santé payée directement par les ménages. |\n"
            "| **Facteur PPP** · `PA.NUS.PPP` | Facteur de conversion à parité de pouvoir d'achat | Unités de monnaie locale par dollar international. |\n"
            "| **PIB par habitant** · `NY.GDP.PCAP.CD` | Produit intérieur brut par habitant | Production économique totale par personne en USD courants. |\n"
            "| **Salaire moyen** · AW | Salaire moyen national | Salaire annuel brut moyen à l'échelle de l'économie ; dénominateur utilisé pour les niveaux de pension et les taux de remplacement. |\n"
            "| **WDI** | Indicateurs du développement mondial | Base de données phare de la Banque mondiale. API : `api.worldbank.org/v2`. |\n"
            "| **ILO / ILOSTAT** | Statistiques de l'Organisation internationale du travail | Base de données mondiale sur les statistiques du travail. API : `sdmx.ilo.org/rest`. |\n"
            "| **WHO GHO** | Observatoire mondial de la santé de l'OMS | Dépôt de données ouvertes de l'OMS pour les statistiques de santé. API : `ghoapi.azureedge.net/api`. |\n"
            "| **UN WPP** | Perspectives de la population mondiale des Nations Unies | Estimations démographiques et projections des Nations Unies. API : `population.un.org/dataportalapi`. |"
        ),
        "glossary_rc_title": "🔢 Termes du calculateur de coût de retraite",
        "glossary_rc_body": (
            "| Terme | Définition |\n"
            "|---|---|\n"
            "| **Horizon de retraite** | Nombre estimé d'années passées à la retraite = espérance de vie résiduelle à l'âge de la retraite. |\n"
            "| **Années en bonne santé** | Part de l'horizon de retraite attendue en bonne santé (d'après la décomposition HALE). |\n"
            "| **Années en mauvaise santé** | Années de retraite avec un handicap significatif ou une maladie chronique ; coûts de santé plus élevés. |\n"
            "| **Niveau de consommation** | Source de données pour la base de coût de vie. Niveau 1 = seuil de pauvreté national ; Niveau 3 = HFCE par habitant. |\n"
            "| **Multiplicateur de scénario** | Coefficient appliqué à la base de consommation : basique (0,55×), modéré (0,75×), confortable (1,0×) du HFCE/habitant. |\n"
            "| **Facteur de majoration par âge** | Multiplicateur appliqué aux dépenses OOP de santé de référence pendant les années en mauvaise santé (défaut 1,5×). |\n"
            "| **Taux d'actualisation** | Taux utilisé pour ramener les coûts futurs à leur valeur actuelle. |\n"
            "| **Taux d'inflation** | Taux auquel les coûts augmentent chaque année. |\n"
            "| **Valeur actuelle totale sur la durée de vie (VA)** | Somme de tous les coûts annuels de retraite actualisés — le capital nécessaire à la date de départ en retraite. |"
        ),
        "glossary_coverage_title": "🌍 Couverture par pays et notes sur les systèmes",
        "glossary_coverage_body": (
            "| Sujet | Note |\n"
            "|---|---|\n"
            "| **Systèmes à deux voies dans le CCG** | L'Arabie saoudite, les Émirats arabes unis, le Koweït, le Qatar, Bahreïn et Oman ont des systèmes parallèles : fonds de pension obligatoires pour les citoyens nationaux ; indemnités de fin de service (EOSB) pour les expatriés. Ce tableau de bord modélise **uniquement le régime national**. |\n"
            "| **EOBI Pakistan** | L'institution des prestations de vieillesse des employés calcule les cotisations sur le **salaire minimum**, et non sur le salaire réel. Cela produit de faibles taux de remplacement effectifs par rapport au salaire moyen pour les travailleurs mieux rémunérés. |\n"
            "| **Couverture des expatriés** | Dans la plupart des pays du CCG, les travailleurs expatriés (souvent la majorité de la main-d'œuvre) sont explicitement exclus du régime de retraite obligatoire. Leur type de travailleur est marqué `excluded` et leur prestation modélisée est nulle. |\n"
            "| **Régimes de la fonction publique** | Plusieurs pays maintiennent des régimes de retraite distincts et plus généreux pour les fonctionnaires. Lorsque les données sont disponibles, ils sont modélisés comme des types de travailleurs distincts. |\n"
            "| **Systèmes multi-piliers** | La plupart des systèmes modernes combinent un pilier PAYG DB (premier pilier), un pilier DC capitalisé (deuxième pilier) et une épargne volontaire (troisième pilier). Tous les piliers présents dans le YAML du pays sont modélisés simultanément. |"
        ),
        "tab_primer": "🔗 Notes WB Primer",
        "primer_intro": "Notes de référence sélectionnées du World Bank Pension Reform Primer sur la conception, le financement et la politique des systèmes de retraite.",
        "deep_profile_header": "Profil pays approfondi",
        "deep_profile_last_updated": "Dernière mise à jour : {date}",
        "deep_profile_narrative_header": "Vue d'ensemble narrative",
        "deep_profile_country_info_header": "Informations au niveau du pays",
        "deep_profile_kpi_header": "Système de retraite de {country}",
        "deep_profile_schemes_header": "Principaux régimes de retraite dans le pays",
        "deep_profile_indicator_label": "Indicateur",
        "deep_profile_indicator_value": "Valeur",
        "deep_profile_indicator_year": "Année",
        "deep_profile_indicator_source": "Source",
        "not_available": "Non disponible",
        "rc_header": "💰 Calculateur du coût de la retraite",
        "rc_subheader": "Estime les coûts annuels et à vie de la retraite à partir de données publiques (Banque mondiale, OMS, UN WPP).",
        "rc_country": "Pays",
        "rc_retirement_age": "Âge de la retraite",
        "rc_sex": "Sexe",
        "rc_scenario": "Scénario",
        "rc_scenario_basic": "Basique",
        "rc_scenario_moderate": "Modéré",
        "rc_scenario_comfortable": "Confortable",
        "rc_discount_rate": "Taux d'actualisation réel",
        "rc_inflation_rate": "Taux d'inflation nominal",
        "rc_age_uplift": "Majoration dépenses de santé (années en mauvaise santé)",
        "rc_include_oop": "Inclure les dépenses de santé à la charge du patient",
        "rc_use_hale": "Utiliser la répartition années saines/malsaines HALE",
        "rc_calculate_btn": "Calculer",
        "rc_calculating": "Récupération des données et calcul en cours…",
        "rc_horizon_header": "Horizon de retraite",
        "rc_annual_header": "Coût annuel",
        "rc_lifetime_header": "Coût à vie (VA)",
        "rc_monthly_income": "Revenu mensuel nécessaire",
        "rc_annual_total": "Total annuel",
        "rc_lifetime_pv": "Valeur actuelle à vie",
        "rc_healthy_years": "Années en bonne santé",
        "rc_unhealthy_years": "Années en mauvaise santé",
        "rc_horizon_method": "Source de l'horizon",
        "rc_consumption_tier": "Niveau de consommation",
        "rc_ratio_gdp": "par rapport au PIB par habitant",
        "rc_ratio_poverty": "par rapport au seuil de pauvreté",
        "rc_ppp_equiv": "Équivalent PPA ($ intl.)",
        "rc_breakdown_title": "Ventilation du coût annuel",
        "rc_consumption_label": "Consommation",
        "rc_oop_label": "Dépenses de santé à la charge du patient",
        "rc_health_years_title": "Années de retraite",
        "rc_sources_header": "Sources de données",
        "rc_proxy_note": "[proxy]",
        "rc_no_le_warning": "Aucune donnée d'espérance de vie trouvée pour ce pays. Impossible de calculer le coût à vie.",
        "rc_no_hfce_warning": "Aucune donnée HFCE ou seuil de pauvreté trouvé. Impossible de calculer la cible de consommation annuelle.",
        "rc_disclaimer": "Estimations uniquement. Ne constitue pas un conseil financier. La disponibilité des données varie selon les pays.",
        "rc_tier1": "Seuil de pauvreté national",
        "rc_tier3": "Consommation des ménages (HFCE)",
        "rc_method_wpp": "UN WPP par âge spécifique",
        "rc_method_gho": "WHO GHO HALE à 60 ans (proxy)",
        "rc_method_none": "Données insuffisantes",
        "overview_header": "🏠 Vue d'ensemble de la base de données",
        "kpi_countries": "Pays modélisés",
        "kpi_avg_grr": "TBR brut moyen @ {n}×SM",
        "kpi_avg_nrr": "TBR net moyen @ {n}×SM",
        "kpi_avg_gpw": "PR brut moyen @ {n}×SM",
        "kpi_avg_nra": "NRA moyen (homme)",
        "errors_expander": "⚠️ {n} pays ont rencontré des erreurs de chargement",
        "map_metric_label": "Indicateur cartographique",
        "opt_gross_rr": "TBR brut",
        "opt_net_rr": "TBR net",
        "opt_gross_pl": "NP brut",
        "opt_net_pl": "NP net",
        "opt_gross_pw": "PR brut",
        "map_title_gross_rr": "Taux brut de remplacement @ {n}×SM",
        "map_title_net_rr": "Taux net de remplacement @ {n}×SM",
        "map_title_gross_pl": "Niveau brut de pension @ {n}×SM",
        "map_title_net_pl": "Niveau net de pension @ {n}×SM",
        "map_title_gross_pw": "Patrimoine brut de retraite @ {n}×SM",
        "summary_table_header": "Tableau récapitulatif",
        "col_iso3": "ISO3",
        "col_wb_level": "Niveau WB",
        "col_gross_rr_at": "TBR brut @ {n}×SM",
        "col_net_rr_at": "TBR net @ {n}×SM",
        "col_gross_pl_at": "NP brut @ {n}×SM",
        "col_gross_pw_at": "PR brut @ {n}×SM",
        "no_data_warning": "Aucune donnée pays disponible.",
        "country_header": "🌍 Profil pays",
        "select_country": "Sélectionner un pays",
        "metric_country": "Pays",
        "metric_nra_mf": "NRA (H / F)",
        "metric_gross_rr_1aw": "TBR brut @ 1×SM",
        "metric_avg_wage": "Salaire moyen",
        "scheme_details_header": "Détails du régime de retraite ({n} régime)",
        "scheme_details_header_plural": "Détails des régimes de retraite ({n} régimes)",
        "results_header": "Résultats de la modélisation des retraites",
        "results_intro": (
            "Ce tableau présente les six indicateurs standard de retraite, chacun calculé à six niveaux "
            "de salaire différents (de la moitié du salaire moyen national jusqu'à 2,5 fois celui-ci).\n\n"
            "**Comment lire les colonnes :** Chaque colonne représente un type de travailleur différent. "
            "Par exemple, **0,5×SM** correspond à un bas salaire, **1,0×SM** au salaire moyen, "
            "et **2,5×SM** à un haut salaire.\n\n"
            "**Comment lire les lignes :**\n"
            "- **Taux brut de remplacement (%)** — La pension en pourcentage du salaire avant la retraite, "
            "*avant* toute déduction fiscale.\n"
            "- **Taux net de remplacement (%)** — Pension nette divisée par les revenus nets avant la retraite.\n"
            "- **Niveau brut de pension (% SM)** — La pension en pourcentage du salaire moyen national, avant impôts.\n"
            "- **Niveau net de pension (% SM)** — La pension après impôts en pourcentage du salaire moyen national.\n"
            "- **Patrimoine brut de retraite (×SM)** — La valeur totale des pensions sur une vie, en multiple du salaire moyen.\n"
            "- **Patrimoine net de retraite (×SM)** — La même valeur à vie, calculée sur les montants après impôts."
        ),
        "download_results_csv": "⬇ Télécharger le CSV des résultats",
        "detailed_results_expander": "Résultats détaillés en monnaie locale (montants absolus)",
        "detailed_results_note": "Tous les montants de pension sont en **{currency}** par an.",
        "col_earnings_aw": "Salaire (×SM)",
        "col_individual_wage": "Salaire individuel",
        "col_gross_pension": "Pension brute",
        "col_net_pension": "Pension nette",
        "col_gross_rr": "TBR brut",
        "col_net_rr": "TBR net",
        "col_gross_pl": "NP brut",
        "col_net_pl": "NP net",
        "col_gross_pw": "PR brut",
        "col_net_pw": "PR net",
        "charts_header": "Graphiques",
        "charts_intro": "Les six graphiques ci-dessous suivent la présentation standard de l'OECD *Panorama des pensions*.",
        "chart_a_caption": "**a. Niveau brut de pension** — Quelle est l'importance de la pension par rapport au salaire moyen national ?",
        "chart_b_caption": "**b. Taux brut de remplacement** — Quelle part de votre salaire la pension remplace-t-elle ?",
        "chart_c_caption": "**c. Niveaux brut et net de pension** — Compare la pension avant impôt (brut) et après impôt (net).",
        "chart_d_caption": "**d. Taux brut et net de remplacement** — Compare les taux de remplacement brut et net.",
        "chart_e_caption": "**e. Impôts payés par les retraités et les travailleurs** — Montre la charge effective sur chaque groupe.",
        "chart_f_caption": "**f. Sources du taux net de remplacement** — Ventilation complète du taux net de remplacement.",
        "chart_a_title": "a. Niveau brut de pension",
        "chart_b_title": "b. Taux brut de remplacement",
        "chart_c_title": "c. Niveaux brut et net de pension",
        "chart_d_title": "d. Taux brut et net de remplacement",
        "chart_e_title": "e. Impôts payés par les retraités et les travailleurs",
        "chart_f_title": "f. Sources du taux net de remplacement",
        "xaxis_earnings": "Revenus individuels (× salaire moyen)",
        "yaxis_gross_pl": "Niveau brut de pension (% salaire moyen)",
        "yaxis_gross_rr": "Taux brut de remplacement (%)",
        "yaxis_pl": "Niveau de pension (% salaire moyen)",
        "yaxis_rr": "Taux de remplacement (%)",
        "yaxis_tax_burden": "Charge fiscale / cotisations (% des revenus/pensions bruts)",
        "yaxis_net_rr": "Taux net de remplacement (%)",
        "yaxis_pension_wealth": "Patrimoine de retraite (× salaire moyen)",
        "trace_gross_pl": "NP brut",
        "trace_net_pl": "NP net",
        "trace_gross_rr": "TBR brut",
        "trace_net_rr": "TBR net",
        "trace_gross_pw": "PR brut",
        "trace_net_pw": "PR net",
        "trace_worker_ee": "Travailleurs – cotisations EE",
        "trace_worker_total": "Travailleurs – charge totale (SSC + impôt sur le revenu)",
        "trace_worker_income": "Travailleurs – impôt sur le revenu",
        "trace_pensioner_tax": "Retraités – impôt sur le revenu",
        "trace_pensioner_total": "Retraités – charge totale (impôt sur le revenu + SSC)",
        "trace_pension_tax_deduction": "Impôt sur le revenu de la pension (−)",
        "trace_worker_wedge": "Coin de cotisation EE travailleur (+)",
        "xaxis_earnings_pension": "Revenus individuels / pension (× salaire moyen)",
        "annotation_100pct_aw": "100 % SM",
        "annotation_100pct": "100 %",
        "label_active": "✅ Actif",
        "label_inactive": "⚠️ Inactif / Perturbé",
        "coverage_prefix": "**Couverture :** {text}",
        "section_eligibility": "**Conditions d'éligibilité**",
        "metric_nra_male": "NRA – Homme",
        "metric_nra_female": "NRA – Femme",
        "metric_era_male": "Ret. anticipée – Homme",
        "metric_era_female": "Ret. anticipée – Femme",
        "metric_min_contrib_yrs": "Années de cotisation minimales",
        "metric_vesting_yrs": "Années d'acquisition des droits",
        "metric_nra_source_m": "Source NRA (H)",
        "metric_nra_source_f": "Source NRA (F)",
        "section_benefit_formula": "**Formule de calcul de la prestation**",
        "section_contributions": "**Cotisations**",
        "section_notes": "**Notes**",
        "row_accrual_rate": "Taux d'accumulation",
        "row_flat_rate": "Taux forfaitaire",
        "row_reference_wage": "Salaire de référence",
        "row_valorisation": "Valorisation",
        "row_indexation": "Indexation post-retraite",
        "row_min_benefit": "Prestation minimale",
        "row_max_benefit": "Prestation maximale",
        "col_parameter": "Paramètre",
        "col_value": "Valeur",
        "col_source": "Source",
        "col_rate": "Taux",
        "contrib_employee": "Taux salarié",
        "contrib_employer": "Taux employeur",
        "contrib_total": "Taux total",
        "contrib_ceiling": "Plafond de salaire",
        "contrib_base": "Assiette de cotisation",
        "contrib_base_default": "salaire brut",
        "non_contributory": "Régime non contributif",
        "ref_career_average": "salaire moyen de carrière",
        "ref_final_salary": "dernier salaire",
        "ref_average_revalued": "salaire moyen de carrière revalorisé",
        "ref_minimum_wage_base": "salaire minimum (assiette plafonnée)",
        "ref_generic": "salaire de référence",
        "formula_db": "**Pension = {pct:.2f}%** × années de service × {ref}",
        "formula_db_min_yrs": "min {yrs} années de cotisation",
        "formula_db_max": "max {pct:.0f}% SM",
        "formula_db_ceiling": "plafond de salaire {mult:.2f}×SM",
        "formula_db_fallback": "Prestations définies – formule non paramétrée",
        "formula_dc": "**Fonds accumulé** ({contrib} du salaire) → {payout} à NRA {nra}",
        "formula_basic": "**Pension forfaitaire = {pct:.1f}%** × salaire moyen (universel, à partir de {nra} ans)",
        "formula_basic_fallback": "Pension universelle à taux forfaitaire à partir de {nra} ans",
        "formula_minimum": "**Complément jusqu'à ≥ {pct:.1f}%** × salaire moyen (appliqué lorsque la prestation liée aux revenus est inférieure au plancher)",
        "formula_minimum_fallback": "Garantie de pension minimale (complément)",
        "formula_points_value": "Points = (salaire / SM) × années de service ; **Pension = points × valeur du point**",
        "formula_points_accrual": "Système par points ; accumulation effective ≈ **{pct:.2f}%**/an × {ref}",
        "formula_points_fallback": "Système par points – voir notes du régime",
        "formula_ndc": "**Compte notionnel** ({contrib} crédité à {rate}) ÷ diviseur de rente à NRA {nra}",
        "formula_targeted": "**Sous conditions de ressources : jusqu'à {pct:.1f}%** × salaire moyen, réduit au-dessus du seuil de revenu",
        "formula_targeted_fallback": "Pension sociale sous conditions de ressources",
        "formula_generic_fallback": "Voir les notes du régime",
        "unit_yrs": " ans",
        "nra_delta": "(H {sign}{diff} vs F)",
        "compare_by_multiple": "par multiple de salaire",
        "payout_annuity": "rente",
        "payout_lump_sum": "capital unique",
        "payout_prog_withdrawal": "retrait programmé",
        "compare_header": "📊 Comparaison entre pays",
        "compare_countries_label": "Pays",
        "compare_metric_label": "Indicateur",
        "compare_multiple_label": "Multiple de salaire",
        "select_one_country": "Sélectionnez au moins un pays.",
        "metric_gross_rr_long": "Taux brut de remplacement",
        "metric_net_rr_long": "Taux net de remplacement",
        "metric_gross_pl_long": "Niveau brut de pension",
        "metric_net_pl_long": "Niveau net de pension",
        "metric_gross_pw_long": "Patrimoine brut de retraite",
        "metric_net_pw_long": "Patrimoine net de retraite",
        "comparison_table_header": "Tableau comparatif",
        "col_country": "Pays",
        "pag_header": "📋 Tableaux de style PAG",
        "pag_intro": "Tableaux comparatifs inspirés de la publication OECD *Panorama des pensions*.",
        "pag_tab_21": "2.1 Structure du système",
        "pag_tab_3x": "3.1–3.4 Paramètres par région",
        "pag_tab_35": "3.5 Salaires et valorisation",
        "pag_tab_36": "3.6 Indexation",
        "pag_tab_51": "5.1 TBR brut",
        "pag_tab_61": "6.1 TBR net",
        "pag_21_header": "Tableau 2.1 – Structure des systèmes de retraite",
        "pag_21_caption": "Classification des régimes de retraite obligatoires par niveau et type.",
        "pag_3x_header": "Tableaux 3.1–3.4 – Résumé des paramètres du système de retraite",
        "pag_3x_region_label": "Filtrer par région Banque mondiale",
        "pag_3x_all_regions": "Toutes les régions",
        "pag_3x_no_data": "Aucune donnée pour la région sélectionnée.",
        "pag_35_header": "Tableau 3.5 – Mesure des salaires et valorisation",
        "pag_35_caption": "Concerne uniquement les régimes liés aux revenus (DB, Points, NDC).",
        "pag_36_header": "Tableau 3.6 – Procédures d'ajustement des pensions en cours de versement",
        "pag_36_caption": "Méthode d'indexation appliquée aux pensions déjà en cours de versement.",
        "pag_51_header": "Tableau 5.1 – Taux bruts de remplacement par niveau de salaire",
        "pag_51_caption": "Pension obligatoire (tous niveaux confondus), brute d'impôts et de cotisations.",
        "pag_51_heatmap_title": "**Carte thermique – Taux brut de remplacement @ 1,0×SM**",
        "pag_61_header": "Tableau 6.1 – Taux nets de remplacement par niveau de salaire",
        "pag_61_caption": "Pension obligatoire nette des impôts sur le revenu et des cotisations sociales.",
        "pag_61_chart_title": "**Taux brut vs net de remplacement @ 1,0×SM**",
        "download_csv": "⬇ Télécharger le CSV",
        "col_pag_country": "Pays",
        "col_pag_iso3": "ISO3",
        "col_pag_region": "Région",
        "col_pag_income": "Revenu",
        "col_tier1": "Niveau 1 (public)",
        "col_tier2": "Niveau 2 (privé)",
        "col_tier3": "Niveau 3 (volontaire)",
        "col_num_schemes": "Nbre de régimes",
        "col_nra_m": "NRA (H)",
        "col_nra_f": "NRA (F)",
        "col_ee_all": "EE % (tous)",
        "col_er_all": "ER % (tous)",
        "col_scheme": "Régime",
        "col_tier": "Niveau",
        "col_type": "Type",
        "col_min_yrs": "Années min.",
        "col_vest_yrs": "Années d'acquisition",
        "col_ee_pct": "EE %",
        "col_er_pct": "ER %",
        "col_total_pct": "Total %",
        "col_ceiling": "Plafond",
        "col_ceiling_none": "Aucun",
        "col_accrual_yr": "Accumulation/an",
        "col_flat_rate": "Taux forfaitaire",
        "col_min_benefit": "Prestation min.",
        "col_max_benefit": "Prestation max.",
        "col_earnings_measure": "Mesure des salaires",
        "col_valorization": "Valorisation",
        "col_accrual_rate_yr": "Taux d'accumulation/an",
        "col_indexation": "Indexation",
        "col_indicator": "Indicateur",
        "val_career_average": "Moyenne de carrière",
        "val_final_salary": "Dernier salaire",
        "val_revalued_career_avg": "Moyenne de carrière revalorisée",
        "val_min_wage_base": "Assiette salaire minimum",
        "val_wages": "Salaires",
        "val_prices": "Prix",
        "val_gdp": "GDP",
        "val_investment_returns": "Rendements des investissements",
        "val_discretionary": "Discrétionnaire",
        "val_fixed_rate": "Taux fixe",
        "val_prices_cpi": "Prix (CPI)",
        "val_mixed": "Mixte (CPI/salaires)",
        "val_na": "—",
        "ind_gross_rr": "Taux brut de remplacement (%)",
        "ind_net_rr": "Taux net de remplacement (%)",
        "ind_gross_pl": "Niveau brut de pension (% SM)",
        "ind_net_pl": "Niveau net de pension (% SM)",
        "ind_gross_pw": "Patrimoine brut de retraite (×SM)",
        "ind_net_pw": "Patrimoine net de retraite (×SM)",
        "pag_gross_rr_pct": "TBR brut @ 1×SM (%)",
        "pag_gross_rr_col": "TBR brut (%)",
        "pag_net_rr_col": "TBR net (%)",
        "chart_rr_xaxis": "Taux de remplacement (%)",
        "methodology_header": "📖 Méthodologie et sources de données",
        "methodology_body": "### Approche de modélisation\n\nLa base de données des retraites suit la méthodologie du **Panorama des pensions de l'OECD**.",
        "methodology_pension_calc_body": "### Objectif\n\nLe **Calculateur de retraite** estime la prestation de retraite pour un individu spécifique.",
        "methodology_rc_body": "### Objectif\n\nLe **Calculateur du coût de la retraite** estime le montant qu'une personne doit épargner avant la retraite.",
    },
}
