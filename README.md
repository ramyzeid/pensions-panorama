# Pensions Panorama

A production-quality Python project that builds a **Pensions-at-a-Glance**-style
comparative dataset and interactive dashboard covering **189 countries**.
It models pension entitlements (replacement rates, pension levels, pension wealth)
from hand-curated YAML parameter files, live API data, and UN life tables —
then serves everything through a 9-tab multilingual Streamlit dashboard.

**Live:** https://pensions.ramyzeid.com
**GitHub:** https://github.com/ramyzeid/pensions-panorama
**Status:** v2.0 · Feb 27, 2026 · 80 tests passing · auto-deploys on push to `main`

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Repository Layout](#repository-layout)
3. [Architecture Overview](#architecture-overview)
4. [Country YAML Parameter Files](#country-yaml-parameter-files)
5. [Data Pipeline](#data-pipeline)
6. [Pension Model](#pension-model)
7. [Dashboard — app.py](#dashboard--apppy)
8. [Dashboard Tab Reference](#dashboard-tab-reference)
9. [i18n — Translation System](#i18n--translation-system)
10. [Deep Profile JSONs](#deep-profile-jsons)
11. [Bulk YAML Enrichment Script](#bulk-yaml-enrichment-script)
12. [CLI Reference](#cli-reference)
13. [Data Sources](#data-sources)
14. [Modeling Assumptions](#modeling-assumptions)
15. [Result Indicators](#result-indicators)
16. [Running the Tests](#running-the-tests)
17. [How to Add a New Country](#how-to-add-a-new-country)
18. [Extending the Model](#extending-the-model)
19. [Dependencies](#dependencies)
20. [Version History](#version-history)

---

## Quick Start

```bash
# Python 3.11+ required. Use pip3 on macOS if pip resolves to a different interpreter.

# 1. Install in editable mode with dev extras
pip install -e ".[dev]"

# 2. Validate country YAML files (fast, no API calls)
pp validate-params --countries JOR MAR

# 3. Run the full pipeline for two countries
pp all --countries JOR MAR --ref-year 2022

# 4. Bulk-enrich all 189 YAMLs with World Bank coverage data (run once)
python scripts/bulk_enrich_yaml.py

# 5. Build deep profile JSONs for the dashboard
pp build-deep-profiles

# 6. Launch the Streamlit dashboard
pp serve
# → http://localhost:8501
```

**Environment variables:**

| Variable | Required | Purpose |
|---|---|---|
| `ANTHROPIC_API_KEY` | Optional | Enables AI Q&A panel in Country Profile (Claude Haiku) |

---

## Repository Layout

```
pensions_panorama/              Python package (installed as `pensions_panorama`)
├── __init__.py
├── config.py                   Path constants, RunConfig Pydantic model, logging setup
├── cli.py                      Typer CLI — all `pp` commands defined here
│
├── schema/
│   ├── params_schema.py        All Pydantic v2 models for country YAML files
│   │                           (CountryParams, SchemeComponent, EligibilityRules,
│   │                            BenefitRules, ContributionRules, WorkerTypeRules,
│   │                            ReformEvent, SourcedValue, …)
│   └── deep_profile_schema.py  Schema for deep profile JSON files
│
├── sources/                    External API clients (all disk-cached via diskcache)
│   ├── worldbank.py            WorldBankClient — WDI, ASPIRE, GFDD indicators
│   ├── un_dataportal.py        UN WPP life tables (lx survivorship, ex life expectancy)
│   └── ilostat_sdmx.py         ILOSTAT SDMX — average earnings by country
│
├── model/                      Core pension computation
│   ├── assumptions.py          GlobalAssumptions loaded from assumptions.yaml
│   ├── calculator.py           PersonProfile dataclass + compute_benefit() entry point
│   ├── pension_engine.py       PensionEngine — dispatches to 7 scheme types,
│   │                           aggregates components, applies tax
│   ├── tax_engine.py           FlatRateTaxEngine + BracketTaxEngine
│   └── pension_wealth.py       PensionWealthCalculator — survival-weighted PV
│
├── reporting/
│   ├── charts.py               Matplotlib static charts (4 per country)
│   ├── export.py               CSV and Excel (multi-sheet) exports
│   └── country_report.py       Jinja2 Markdown country briefs
│
├── deep_profile/
│   └── builder.py              DeepProfileBuilder — fetches live indicators,
│                               merges mapping YAML overrides, writes JSON
│
├── retirement_cost/
│   ├── engine.py               RetirementCostEngine — lifetime cost calculator
│   ├── connectors.py           API connectors for WHO HALE, WB health spending
│   └── types.py                RetirementCostResult dataclass
│
├── templates/
│   └── country_report.md.j2    Jinja2 template for Markdown country briefs
│
└── web/
    ├── app.py                  Streamlit dashboard (5,137 lines) — all tabs + helpers
    └── i18n.py                 Translation strings — EN / AR / FR (420 keys each)

scripts/
└── bulk_enrich_yaml.py         One-shot enrichment: WB coverage_rate + reform_status

data/
├── params/
│   ├── assumptions.yaml        Global modeling assumptions (entry age, discount rate, …)
│   ├── _template.yaml          Blank country template
│   └── <ISO3>.yaml             One YAML per country — 189 files total
├── deep_profiles/
│   └── <ISO3>.yaml             Optional per-country mapping overrides (narrative, KPIs, …)
├── raw/
│   └── cache/                  Disk-cached API responses
│       ├── worldbank/          World Bank responses (TTL: 7 days)
│       ├── ilostat/            ILOSTAT responses (TTL: 7 days)
│       └── un_dataportal/      UN WPP responses (TTL: 30 days)
└── processed/                  Cleaned Parquet datasets (intermediate outputs)

reports/
├── country/<ISO3>/             Per-country outputs (CSV, Excel, PNGs, .md)
├── deep_profiles/<ISO3>.json   Committed pre-built deep profile JSONs (189 files)
└── panorama_summary/           Cross-country summary (CSV, Excel, Markdown)

tests/
├── conftest.py                 Shared fixtures (sample params, mock API responses)
├── test_schema.py              Pydantic schema validation tests
├── test_pension_engine.py      Engine unit tests — all 7 scheme types
├── test_calculator.py          PersonProfile + compute_benefit() integration tests
├── test_worker_types.py        Worker type eligibility and override tests
├── test_deep_profile.py        DeepProfileBuilder tests
└── test_worldbank.py           WorldBankClient tests with mocked HTTP (responses lib)
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATA LAYER                               │
│                                                                 │
│  data/params/<ISO3>.yaml   ──►  params_schema.py (Pydantic)    │
│  data/params/assumptions.yaml  ──►  GlobalAssumptions          │
│                                                                 │
│  WorldBankClient  ──► WDI / ASPIRE / GFDD (disk-cached)        │
│  ILOSTATClient    ──► Average earnings     (disk-cached)        │
│  UNDataPortal     ──► Life tables          (disk-cached)        │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                      MODEL LAYER                                │
│                                                                 │
│  PensionEngine.compute_benefit(PersonProfile)                   │
│    ├── _dispatch() → scheme-type handler × N schemes            │
│    │     DB / NDC / DC / basic / targeted / minimum / points    │
│    ├── _aggregate() → sum components                            │
│    ├── _apply_tax() → FlatRate or Bracket engine                │
│    └── PensionWealthCalculator → survival-weighted PV           │
│                                                                 │
│  Evaluated at 6 earnings multiples: 0.5 / 0.75 / 1.0 /         │
│  1.5 / 2.0 / 2.5 × national average wage                       │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                    OUTPUT LAYER                                  │
│                                                                 │
│  reports/country/<ISO3>/    CSV · Excel · PNGs · Markdown       │
│  reports/panorama_summary/  Cross-country CSV · Excel           │
│  reports/deep_profiles/     Pre-built JSON for dashboard        │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                   DASHBOARD LAYER  (web/app.py)                 │
│                                                                 │
│  load_all_data() → runs PensionEngine for every country         │
│  build_summary_df() → summary DataFrame for overview/compare    │
│  9 @st.fragment tabs ──► see Tab Reference below               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Country YAML Parameter Files

Every country is described by a single YAML file at `data/params/<ISO3>.yaml`.
The Pydantic models in `params_schema.py` validate every field on load.

### Top-level structure

```yaml
metadata:
  country_name: "Jordan"
  iso3: "JOR"
  iso2: "JO"
  currency: "Jordanian Dinar"
  currency_code: "JOD"
  reference_year: 2023
  wb_region: "MEA"
  wb_income_level: "UMC"   # HIC | UMC | LMC | LIC
  un_location_id: 400       # UN WPP location ID (for life tables)
  sources: [...]
  last_reviewed: "2024-01-15"

schemes:
  - scheme_id: "SSC_OAI"
    name: "SSC Old-Age Insurance"
    tier: "first"           # zero | first | second | third | fourth
    type: "DB"              # DB | NDC | DC | basic | targeted | minimum | points
    active: true
    reform_status: "stable" # stable | reform_pending | recently_reformed | under_review
    eligibility: { ... }
    contribution_rate: { ... }
    benefit_formula: { ... }
    payout: { ... }

worker_types:
  private_employee:
    label: "Private sector employee"
    coverage_status: "covered"   # covered | excluded | partial | unknown
    scheme_ids: ["SSC_OAI"]
    notes: "..."
  self_employed:
    label: "Self-employed"
    coverage_status: "partial"
    scheme_ids: ["SSC_OAI"]

average_earnings:
  ilostat_series_id: "EAR_4MTH_SEX_ECO_CUR_NB_A"
  manual_value: 9600
  manual_currency: "JOD"
  manual_year: 2022

tax_and_contributions:
  simplified_net_rate: 0.10
  # OR use bracket engine:
  brackets:
    - threshold: 12000
      rate: 0.05
    - threshold: 20000
      rate: 0.10

coverage_rate:
  value: 0.38
  source_citation: "World Bank ASPIRE per_si_cp.cov_pop_tot, 2021."
  year: 2021

reforms:
  - year: 2014
    title: "New Social Security Law"
    type: "formula"          # nra | contribution_rate | formula | coverage | merger | indexation | other
    description: "..."
    source_url: "https://..."
```

### SourcedValue pattern

Every numeric parameter uses the `SourcedValue` wrapper to enforce citation:

```yaml
normal_retirement_age_male:
  value: 60
  source_citation: "SSC Law No. 1/2014 Art. 47"
  source_url: "https://www.ssc.gov.jo"
  year: 2023
```

### Scheme types supported

| Type | Engine logic |
|---|---|
| `DB` | `accrual_rate × min(service_years, max_years) × reference_wage` |
| `NDC` | `notional_account_balance / annuity_divisor` |
| `DC` | `accumulated_fund / annuity_divisor` (fund = contribs compounded at real return) |
| `points` | `(wage / AW) × points_per_year × years × point_value` |
| `basic` | Fixed flat amount (optionally indexed to AW) |
| `targeted` | `max_benefit − taper_rate × (wage − threshold)` — phases out with income |
| `minimum` | Top-up: applied if total benefit < floor |

Multi-pillar systems are modelled by listing multiple schemes; the engine runs
all active schemes for a worker type and sums them.

---

## Data Pipeline

```
pp all --countries JOR --ref-year 2022
  │
  ├── pp fetch-data
  │     ├── WorldBankClient.fetch_indicator(...)   → data/raw/cache/worldbank/
  │     ├── ILOSTATClient.fetch_earnings(...)      → data/raw/cache/ilostat/
  │     └── UNDataPortal.fetch_life_table(...)     → data/raw/cache/un_dataportal/
  │
  ├── pp validate-params
  │     └── load_country_params(<ISO3>.yaml)       → Pydantic validation
  │
  ├── pp run
  │     ├── load_assumptions(assumptions.yaml)
  │     ├── _resolve_wage(params, ref_year)        → avg wage from ILOSTAT or manual
  │     └── for mult in [0.5, 0.75, 1.0, 1.5, 2.0, 2.5]:
  │           PensionEngine.compute_benefit(PersonProfile(...))
  │               → PensionResult{gross_rr, net_rr, gross_pl, net_pl, gross_pw, net_pw}
  │
  ├── pp build-reports
  │     ├── charts.py   → 4 Matplotlib PNGs per country
  │     ├── export.py   → CSV + Excel
  │     └── country_report.py → Jinja2 Markdown brief
  │
  └── pp build-deep-profiles
        ├── DeepProfileBuilder.build(iso3)
        │     ├── Fetch live WDI / ASPIRE / GFDD indicators
        │     ├── Merge data/deep_profiles/<ISO3>.yaml overrides
        │     └── Write reports/deep_profiles/<ISO3>.json
        └── Dashboard reads these JSONs at startup
```

---

## Pension Model

### Entry point: `PersonProfile`

Defined in `model/calculator.py`. All fields passed to `PensionEngine.compute_benefit()`.

```python
@dataclass
class PersonProfile:
    sex: str                         # "male" | "female"
    age: float                       # current age (years)
    service_years: float             # years of contributions
    wage: float                      # annual wage
    wage_unit: str = "currency"      # "currency" | "aw_multiple"
    worker_type_id: str = "private_employee"
    contribution_years: float | None = None
    dc_account_balance: float | None = None  # DC balance override
    extra: dict = field(default_factory=dict)
```

### PensionResult

```python
@dataclass
class PensionResult:
    earnings_multiple: float
    individual_wage: float
    gross_benefit: float
    net_benefit: float
    gross_replacement_rate: float
    net_replacement_rate: float
    gross_pension_level: float
    net_pension_level: float
    gross_pension_wealth: float
    net_pension_wealth: float
    component_breakdown: dict[str, float]
    eligibility: EligibilityResult
    reasoning_trace: list[ReasoningStep]
    warnings: list[str]
```

### Pension wealth

Computed by `PensionWealthCalculator` using UN WPP age-specific life tables
(survivorship `lx`, remaining life expectancy `ex`). Falls back to a simplified
annuity formula when UN data is unavailable.

```
GPW = Σ [ gross_benefit × lx(t) / lx(NRA) × (1+g)^t / (1+r)^t ]
```

where `g` = real pension growth rate, `r` = real discount rate, sum over
post-retirement years weighted by survival probability.

---

## Dashboard — app.py

**File:** `pensions_panorama/web/app.py` — 5,137 lines
**Run:** `pp serve` or `streamlit run pensions_panorama/web/app.py`

### Startup sequence

```python
def main():
    ref_year, sex, overview_multiple, multiples = _sidebar()
    # CSS injections (RTL, dark mode, editorial fonts)
    data = load_all_data(ref_year, sex, multiples)   # @st.cache_data
    summary_df = build_summary_df(data, overview_multiple)
    # Render 9 tabs, each as @st.fragment for independent re-rendering
```

### `load_all_data(ref_year, sex, multiples)` → `dict`

Cached. Loops all 189 country YAMLs, runs `PensionEngine` for every
earnings multiple, and returns:

```python
{
  "JOR": {
    "params": CountryParams,
    "results": list[PensionResult],   # one per multiple × sex
    "avg_wage": float,
    "error": str | None,
  },
  ...
}
```

### Cached helper functions (all `@st.cache_data`)

| Function | Purpose | Tab used in |
|---|---|---|
| `load_all_data()` | All country calculations | All tabs |
| `build_summary_df()` | Cross-country DataFrame | Overview, Compare |
| `load_female_data_1aw()` | Female GRR at 1×AW | Country Profile |
| `load_deep_profiles()` | All deep profile JSONs | Country Profile |
| `_fiscal_sustainability_fig()` | Fiscal scatter plot | Country Profile |
| `_build_peer_benchmark_chart()` | Peer bar chart | Country Profile |
| `_convergence_scatter_fig()` | NRA vs GRR scatter | Compare |
| `_system_type_choropleth_fig()` | World map choropleth | Overview |
| `_rr_sensitivity_fig()` | GRR vs service years | Country Profile |
| `_progressivity_chart()` | Progressivity bar chart | Compare |
| `_nra_distribution_fig()` | NRA histogram | Overview |
| `_parameter_heatmap_fig()` | Cross-country heatmap | Compare |
| `_project_pension()` | Personal projector | Calculator |
| `_country_qa_response()` | Claude Haiku Q&A (TTL 1hr) | Country Profile |
| `_fetch_retirement_data()` | WHO/WB health data (TTL 1hr) | Retirement Cost |
| `_build_table_21/3x/35/36/rr_matrix()` | PAG table builders | PAG Tables |

### Theme system

- Dark/light toggle stored in `st.session_state["dark_mode"]`
- `_plotly_template()` returns `"plotly_dark"` or `"plotly_white"`
- `_apply_theme_css()` injects full CSS for both modes
- `_apply_rtl_css()` adds RTL layout when Arabic is selected
- `_apply_emoji_font_css()` loads Playfair Display + Inter + Noto Color Emoji

### Income group colours (used across all charts)

```python
_INCOME_COLORS = {
    "HIC": "#2ca02c",   # green
    "UMC": "#1f77b4",   # blue
    "LMC": "#ff7f0e",   # orange
    "LIC": "#d62728",   # red
}
```

---

## Dashboard Tab Reference

### 🏠 Database (`tab_overview`)

- Summary KPIs: countries loaded, avg GRR, avg NRR, avg GPW, avg NRA
- Sortable summary table with GRR, NRR, GPL, GPW for every country
- Choropleth world map coloured by dominant scheme type (DB/NDC/DC/points/basic/targeted)
- **F6: NRA Distribution histogram** — male NRA across all countries, coloured by income group, with mean line

### 🌍 Country Profile (`tab_country`)

Single scrollable page with 19 sections:

| # | Section | Data source |
|---|---|---|
| 1 | Country selector + header KPIs | YAML params |
| 2 | Narrative overview | Deep profile JSON |
| 3 | Country Level Information (indicator table) | WDI / ASPIRE / GFDD via deep profile |
| 4 | System KPIs | Deep profile JSON |
| 5 | Coverage & Adequacy KPIs (coverage_rate, informality, elderly poverty) | YAML params |
| 6 | Gender pension gap | Engine (male) + cached female run |
| 7 | Fiscal sustainability RAG + scatter | Deep profile indicators |
| 8 | Peer benchmarking bar chart | Engine results across income group |
| 9 | Scheme parameter cards (expandable) | YAML params |
| 10 | **F4: RR Sensitivity** (expander) | Engine, 5–50 service years |
| 11 | **F9: Adequacy Gap** — full-career vs zero contributions | Engine |
| 12 | Modeling Results table | Engine results |
| 13 | 6 PAG-style Plotly charts | Engine results |
| 14 | **F5: PDF Export** | fpdf2, all of the above |
| 15 | Inline calculators (pension + retirement cost) | Engine + health APIs |
| 16 | Main Pension Schemes table | Deep profile JSON |
| 17 | SSA International Updates | Committed JSON index |
| 18 | Reform Timeline | YAML `reforms` list |
| 19 | **F8: AI Q&A** | Claude Haiku (anthropic SDK) |

### 📊 Compare (`tab_compare`)

- Country multiselect + metric selector + earnings multiple slider
- Bar chart + line chart across selected countries
- Comparison table (all 6 multiples)
- Convergence scatter: NRA (x) vs GRR at 1×AW (y), coloured by income group
- **F7: Progressivity chart** — GRR(0.5×AW) ÷ GRR(2.0×AW), sorted descending
- **F2: Parameter Heatmap** — user selects NRA M/F, employee rate, employer rate, or GRR 1×AW; heatmap across all countries sorted by value

### 📖 Methodology (`tab_methodology`)

Static explanatory content: OECD model description, pension calculator notes,
retirement cost calculator notes. Content lives in `i18n.py` (multi-line strings).

### 📋 PAG Tables (`tab_pag_tables`)

Five sub-tabs replicating OECD Pensions at a Glance table format:

| Table | Contents |
|---|---|
| Table 2.1 | Pension system parameters (NRA, contribution rates, accrual, caps) |
| Table 3.x | Gross replacement rates at 6 earnings multiples (filterable by region) |
| Table 3.5 | Gross pension levels (% of AW) |
| Table 3.6 | Indexation and adjustment rules |
| Table 5.1 | Gross replacement rates + heatmap |
| Table 6.1 | Net replacement rates + gross vs net comparison chart |

### 🧮 Pension Calculator (`tab_calculator`)

- Country → worker type → sex, age, service years, wage → Calculate
- Displays: eligibility check, GRR/NRR/GPL/NPL, component breakdown bar, reasoning trace, JSON download
- Two-country side-by-side comparison (same worker profile)
- **F3: Personal Pension Projector**:
  - Inputs: country, birth year, starting wage, real wage growth %, contribution density
  - Outputs: projected wage at NRA, GRR, gross/net annual pension, NRA, effective service years
  - DC trajectory line chart (if country has a DC pillar)

### 💰 Retirement Cost (`tab_retirement_cost`)

Estimates how much a person needs to save to fund retirement:
- Retirement horizon from UN WPP life tables (fallback: WHO HALE at 60)
- Splits into healthy/unhealthy years using HALE data
- Living cost baseline from WB HFCE per capita (3 consumption tiers)
- Health OOP costs from WHO health expenditure data
- Outputs: monthly income needed, annual total, lifetime PV (local currency + PPP USD)
- API sources cited inline with proxy flag if approximations used

### 📖 Glossary (`tab_glossary`)

Six expandable sections (EN/FR/AR):
- Pension Indicators (GRR, NRR, GPL, NPL, GPW, NPW, NRA, ERA, …)
- Scheme Types (DB, DC, NDC, points, basic, targeted, minimum, EOSB, PAYG, funded)
- Life Expectancy & Health (LE, HALE, longevity risk, survival-weighted PV)
- Economic & Data Indicators (HFCE, CHE, OOP, PPP, GDP, WDI, ILO, WHO GHO, UN WPP, PIP)
- Retirement Cost Calculator Terms
- Country Coverage & System Notes (GCC dual-track, Pakistan EOBI, expatriate coverage, civil servants)

### 🔗 WB Primer Notes (`tab_primer`)

Curated links to World Bank Pension Reform Primer notes across 5 categories:
Foundations, System Design, Operational Issues, Policy Levers, Key Reference Books.

### Sidebar (`_sidebar`)

- Language selector (EN / FR / AR) — stored in `st.session_state["lang"]`
- Dark mode toggle — stored in `st.session_state["dark_mode"]`
- Reference year selector (2019–2023)
- Modeled sex radio (male / female / all M+F average)
- Overview earnings multiple slider (0.5–2.5×AW)
- **F10: Live Data Sync** — clears `WB_CACHE_DIR`, `ILO_CACHE_DIR`, `UN_CACHE_DIR` via `shutil.rmtree`, calls `st.cache_data.clear()`, timestamps the refresh

---

## i18n — Translation System

**File:** `pensions_panorama/web/i18n.py`

```python
TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": { "key": "English string", ... },   # 420 keys
    "ar": { "key": "Arabic string",  ... },   # 420 keys
    "fr": { "key": "French string",  ... },   # 420 keys
}
```

Usage in `app.py`:

```python
def t(key: str, **kwargs) -> str:
    lang = st.session_state.get("lang", "en")
    text = TRANSLATIONS.get(lang, {}).get(key) or TRANSLATIONS["en"].get(key, key)
    return text.format(**kwargs) if kwargs else text
```

**Adding new keys:** Add to all three language blocks simultaneously.
The fallback chain is `current_lang → en → key_name_itself`, so a missing
translation never raises an exception — it just shows the key name.

---

## Deep Profile JSONs

Pre-built per-country JSON files committed at `reports/deep_profiles/<ISO3>.json`.
They power the narrative, KPI, and scheme overview sections of the Country Profile.

### Build commands

```bash
pp build-deep-profiles                       # all 189 countries
pp build-deep-profiles --countries "JOR MAR" # specific countries
pp build-deep-profiles --offline             # no network; cached data only
```

### JSON structure

```json
{
  "iso3": "JOR",
  "country_name": "Jordan",
  "last_updated": "2024-01-15T00:00:00",
  "narrative": {
    "text": "Jordan's pension system ...",
    "sources": [{"source_name": "...", "source_url": "..."}]
  },
  "country_indicators": [
    {
      "key": "gdp_per_capita_usd",
      "label": "GDP per capita (USD)",
      "cell": {"value": 4284, "year": 2022, "unit": "USD"}
    }
  ],
  "system_kpis": [
    {
      "label": "Contributory pension coverage",
      "cell": {"value": "38.4%", "year": 2021,
                "source": {"source_name": "World Bank ASPIRE"}}
    }
  ],
  "schemes": [...],
  "ssa_updates": [
    {"date": "2023-03", "title": "...", "url": "...", "topic": "..."}
  ]
}
```

### Mapping overrides

Per-country hand-curated overrides at `data/deep_profiles/<ISO3>.yaml`.
Any field here overrides the auto-generated value. Start from `_template.yaml`.

---

## Bulk YAML Enrichment Script

**File:** `scripts/bulk_enrich_yaml.py`
**Run once** after initial setup or to refresh coverage data.

```bash
python scripts/bulk_enrich_yaml.py
```

**Logic:**

1. Loops `data/params/*.yaml` — skips `assumptions.yaml` and `_template.yaml`
2. **Skips** any file that already has `coverage_rate` (protects hand-curated data)
3. Calls `WorldBankClient.fetch_indicator(iso3, "per_si_cp.cov_pop_tot", 2010, 2023)`
4. Takes the most-recent non-null value; clamps to [0, 1] (some WB values are 0–100)
5. Writes structured `coverage_rate` block with value, year, citation
6. Adds `reform_status: stable` to any active scheme missing that field
7. Backs up original → writes new YAML → validates via `load_country_params()` (Pydantic)
8. On Pydantic failure: restores backup, logs error
9. Prints: `Updated N | Skipped N | Errors N`

---

## CLI Reference

```
pp --help

Commands:
  pp all                   Full pipeline: fetch → validate → run → report
  pp fetch-data            Pull and cache API data for specified countries
  pp validate-params       Pydantic-validate all country YAML files
  pp run                   Run pension calculations; write CSV + Excel
  pp build-reports         Generate Matplotlib charts and Markdown briefs
  pp build-deep-profiles   Build deep profile JSONs for the dashboard
  pp list-countries        List all countries with YAML files
  pp wb-filter-region      List ISO3 codes for a World Bank region
  pp serve                 Launch the Streamlit dashboard
```

**Common flags** (most commands accept all of these):

```
--countries JOR MAR …    ISO3 codes to process (omit for all 189)
--ref-year 2022          Reference year for calculations
--config run_config.yaml Path to run config (overrides defaults)
--params-dir data/params Country YAML directory
--output-dir reports/    Report output directory
--offline                Skip all network calls; use cached data only
```

**`run_config.yaml`** — project-level defaults:

```yaml
countries: [JOR, MAR]
ref_year: 2022
start_year: 2010
end_year: 2022
earnings_multiples: [0.5, 0.75, 1.0, 1.5, 2.0, 2.5]
sex: "male"
cache_ttl_days: 30
log_level: "INFO"
assumptions_file: "assumptions.yaml"
```

---

## Data Sources

| Source | What is fetched | Indicator codes | Cache TTL |
|---|---|---|---|
| **ILOSTAT SDMX** | National average wage | `EAR_4MTH_SEX_ECO_CUR_NB_A` | 7 days |
| **World Bank WDI** | GDP per capita, population 65+ | `NY.GDP.PCAP.CD`, `NY.GDP.PCAP.KN`, `SP.POP.65UP.TO`, `SP.POP.65UP.TO.ZS` | 7 days |
| **World Bank ASPIRE** | Pension + social insurance coverage | `per_si_cp.cov_pop_tot`, `per_si_allsi.cov_pop_tot` | 7 days |
| **World Bank GFDD** | Pension fund assets / GDP | `GFDD.DI.13` | 7 days |
| **UN WPP Data Portal** | Life tables (survivorship, remaining LE) | Indicator 28 (lx), Indicator 75 (ex) | 30 days |
| **WHO GHO** | HALE at 60 (retirement cost fallback) | `WHOSIS_000007` | 7 days |
| **WHO / WB** | Health OOP spending, HFCE per capita | `SH.XPD.OOPC.CH.ZS`, `NE.CON.PRVT.PC.KD`, `PA.NUS.PPP` | 7 days |

All World Bank calls go through `WorldBankClient` in `sources/worldbank.py`
which wraps `requests` with `tenacity` retries (4 attempts, exponential backoff)
and `diskcache` for disk persistence.

**Cache management:** Use the **Refresh live data** button in the dashboard
sidebar, or delete directories under `data/raw/cache/` manually.

---

## Modeling Assumptions

Stored in `data/params/assumptions.yaml`. Loaded by `model/assumptions.py`.

| Parameter | Default | Notes |
|---|---|---|
| Entry age | 20 | OECD standard |
| Career length | 40 years | OECD standard |
| Contribution density | 1.0 (100%) | Full career; adjustable in calculator |
| Real wage growth | 2%/yr | OECD standard |
| Real discount rate | 2%/yr | For pension wealth PV |
| DC net real return | 3%/yr | Net of fees |
| Annuity divisor | From UN WPP life table | Fallback: simplified formula |
| WPP projection year | 2020 | Most recent 2020-2030 projection |

---

## Result Indicators

Computed for each of the 6 earnings multiples (0.5 / 0.75 / 1.0 / 1.5 / 2.0 / 2.5 × AW):

| Indicator | Abbreviation | Formula |
|---|---|---|
| Gross pension level | GPL | Gross annual pension ÷ national average wage |
| Net pension level | NPL | Net annual pension ÷ average net wage |
| Gross replacement rate | GRR | Gross annual pension ÷ individual pre-retirement wage |
| Net replacement rate | NRR | Net annual pension ÷ individual net pre-retirement wage |
| Gross pension wealth | GPW | Survival-weighted PV of gross benefit stream ÷ AW |
| Net pension wealth | NPW | Survival-weighted PV of net benefit stream ÷ AW |

---

## Running the Tests

```bash
pytest tests/ -v          # all 80 tests
pytest tests/ -q          # quiet summary
pytest tests/test_pension_engine.py -v    # specific module
```

**Test coverage:**

| Test file | What it covers |
|---|---|
| `test_schema.py` | Valid YAML loads; invalid fields rejected by Pydantic |
| `test_pension_engine.py` | All 7 scheme types, multi-pillar aggregation, tax |
| `test_calculator.py` | `PersonProfile` → `compute_benefit()` end-to-end |
| `test_worker_types.py` | Coverage status, scheme filtering, excluded workers |
| `test_deep_profile.py` | `DeepProfileBuilder` output structure and indicator fetch |
| `test_worldbank.py` | `WorldBankClient` with `responses`-mocked HTTP calls |

**Note on pip:** On macOS, if `pip` points to a different Python than `python3`,
install with `pip3` to ensure packages land in the correct interpreter.

---

## How to Add a New Country

```bash
# 1. Create a YAML from the template
cp data/params/_template.yaml data/params/EGY.yaml

# 2. Fill in all required fields — every numeric value needs source_citation.
#    Minimum required fields:
#    - metadata (iso3, iso2, currency_code, wb_income_level, un_location_id)
#    - at least one active scheme with eligibility + contribution_rate + benefit_formula
#    - average_earnings (manual_value or ilostat_series_id)
#    - tax_and_contributions (simplified_net_rate or brackets)
#    - worker_types with at least private_employee

# 3. Validate
pp validate-params --countries EGY

# 4. Run calculations
pp all --countries EGY --ref-year 2023

# 5. Build the deep profile JSON
pp build-deep-profiles --countries EGY

# 6. Optionally hand-curate narrative + KPIs
cp data/deep_profiles/_template.yaml data/deep_profiles/EGY.yaml
# edit EGY.yaml, then rebuild:
pp build-deep-profiles --countries EGY --offline

# 7. Commit both files
git add data/params/EGY.yaml reports/deep_profiles/EGY.json
git commit -m "Add Egypt pension parameters"
```

---

## Extending the Model

### Adding a country-specific tax bracket engine

```python
# pensions_panorama/model/tax_engine.py already has BracketTaxEngine.
# In the country YAML, use the `brackets` field under tax_and_contributions:

tax_and_contributions:
  brackets:
    - threshold: 15000   # income up to this is taxed at this rate
      rate: 0.00
    - threshold: 30000
      rate: 0.10
    - threshold: null    # null = infinity (top bracket)
      rate: 0.275
  basic_allowance: 9000
  employee_social_contrib_rate: 0.07
```

### Adding a new scheme type

1. Add the new type string to `SchemeType` enum in `params_schema.py`
2. Add a `_handle_<type>()` method to `PensionEngine` in `pension_engine.py`
3. Register it in `PensionEngine._dispatch()`
4. Add test cases to `test_pension_engine.py`

### Adding a new chart to the dashboard

1. Write a `@st.cache_data` function that takes JSON-serialisable args and returns `go.Figure`
2. Call `_plotly_template()` for the theme and `_INCOME_COLORS` for colour consistency
3. Wire it into the appropriate `tab_*()` function
4. Add i18n keys for the header and caption in all three language blocks

---

## Dependencies

Full list in `pyproject.toml`. Python 3.11+ required.

| Package | Version | Purpose |
|---|---|---|
| `pydantic` | ≥2.5 | YAML schema validation |
| `pydantic-settings` | ≥2.1 | Settings management |
| `typer[all]` | ≥0.9 | CLI |
| `streamlit` | ≥1.28 | Dashboard |
| `plotly` | ≥5.18 | Interactive charts |
| `requests` | ≥2.31 | HTTP API calls |
| `tenacity` | ≥8.2 | Retry logic for API calls |
| `diskcache` | ≥5.6 | Disk-based API response cache |
| `requests-cache` | ≥1.1 | Secondary caching layer |
| `pandas` | ≥2.1 | Data manipulation |
| `numpy` | ≥1.26 | Numeric operations |
| `pyarrow` | ≥14.0 | Parquet read/write |
| `PyYAML` | ≥6.0 | YAML parsing |
| `matplotlib` | ≥3.8 | Static chart generation |
| `openpyxl` | ≥3.1 | Excel export |
| `jinja2` | ≥3.1 | Markdown report templating |
| `tabulate` | ≥0.9 | Table formatting |
| `python-dateutil` | ≥2.8 | Date parsing |
| `rich` | ≥13.7 | CLI output formatting |
| `anthropic` | ≥0.30 | AI Q&A via Claude Haiku (`ANTHROPIC_API_KEY` required) |
| `fpdf2` | ≥2.7 | PDF country report generation |
| `kaleido` | ≥0.2 | Plotly → PNG for PDF embedding |

**Dev extras** (`pip install -e ".[dev]"`):
`pytest`, `pytest-cov`, `responses`, `black`, `ruff`, `mypy`, `types-PyYAML`, `types-requests`

---

## Version History

### v2.0 — Feb 27, 2026

10 new features added in a single session:

| ID | Feature | File(s) changed | Where in UI |
|---|---|---|---|
| F1 | Bulk YAML enrichment (WB coverage + reform_status) | `scripts/bulk_enrich_yaml.py` (new) | CLI script |
| F2 | Cross-country parameter heatmap | `app.py` | Compare tab |
| F3 | Personal Pension Projector | `app.py` | Calculator tab |
| F4 | Replacement Rate Sensitivity chart | `app.py` | Country Profile |
| F5 | PDF country report download | `app.py` (fpdf2) | Country Profile |
| F6 | NRA global distribution histogram | `app.py` | Overview tab |
| F7 | Progressivity chart | `app.py` | Compare tab |
| F8 | AI Q&A (Claude Haiku) | `app.py` (anthropic) | Country Profile |
| F9 | Contributory vs Zero-Contribution adequacy gap | `app.py` | Country Profile |
| F10 | Live data sync (sidebar cache-clear) | `app.py` | Sidebar |

Supporting: `i18n.py` (+52 keys × 3 languages = 420 total per language),
`pyproject.toml` (+anthropic, fpdf2, kaleido), `README.md` (full rewrite).

### v1.x — through Feb 26, 2026

- 9-tab Streamlit dashboard with dark mode, RTL Arabic, editorial typography
- 189 country YAML files + deep profile JSONs
- World Bank pillar framework (28 schemes across 25 countries)
- SSA International Updates integration (40 countries, 5-year index)
- Gender pension gap, fiscal sustainability RAG, peer benchmarking
- Retirement Cost tab with HALE-based healthy/unhealthy split
- PAG Tables (5 OECD-style comparative tables)
- 3-language support: EN / FR / AR across all tabs
- 80 automated tests
