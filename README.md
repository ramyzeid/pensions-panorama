# Pensions Database

A production-quality, reproducible Python project that generates
**Pensions-at-a-Glance**-style comparative datasets and country briefs
for a user-specified set of countries.

**Live at: https://pensions.ramyzeid.com**
**GitHub: https://github.com/ramyzeid/pensions-panorama**

---

## Quick Start

```bash
# 1. Install (editable, with dev extras)
pip install -e ".[dev]"

# 2. Validate the sample country parameter files
pp validate-params --countries JOR MAR

# 3. Run the full pipeline for those countries
pp all --countries JOR MAR --ref-year 2022 --config run_config.yaml

# 4. Outputs land in reports/country/<ISO3>/ and reports/panorama_summary/

# 5. Bulk-enrich YAML files with World Bank coverage data (run once)
python scripts/bulk_enrich_yaml.py

# 6. Launch the dashboard
pp serve
```

---

## Repository Layout

```
pensions_panorama/          Python package
├── config.py               Path constants and RunConfig Pydantic model
├── cli.py                  Typer CLI (command: pp)
├── schema/
│   └── params_schema.py    Pydantic v2 models for country YAML files
├── sources/
│   ├── worldbank.py        World Bank Indicators API client (WDI + ASPIRE + GFDD)
│   ├── un_dataportal.py    UN WPP Data Portal API client (life tables)
│   └── ilostat_sdmx.py     ILOSTAT SDMX API client (average earnings)
├── model/
│   ├── assumptions.py      Global modeling assumptions (YAML-backed)
│   ├── pension_engine.py   Gross entitlement calculator (DB/NDC/DC/basic/…)
│   ├── tax_engine.py       Net-of-tax calculations (flat + bracket engines)
│   └── pension_wealth.py   Survival-weighted PV via UN life tables
├── reporting/
│   ├── charts.py           Matplotlib charts (4 standard plots per country)
│   ├── export.py           CSV and Excel exports
│   └── country_report.py   Jinja2-rendered Markdown reports
└── templates/
    └── country_report.md.j2

scripts/
└── bulk_enrich_yaml.py     One-shot: adds WB coverage_rate + reform_status to YAMLs

data/
├── params/
│   ├── assumptions.yaml    Global modeling assumptions
│   ├── _template.yaml      Blank country template (start here)
│   └── <ISO3>.yaml         One file per country (189 total)
├── deep_profiles/          Per-country mapping YAMLs (narrative, scheme overrides)
├── raw/cache/              Disk-cached API responses (timestamped)
└── processed/              Cleaned datasets in Parquet

reports/
├── country/<ISO3>/         One folder per country (CSV, Excel, charts, .md)
├── deep_profiles/<ISO3>.json  Pre-built country deep profile data (committed)
└── panorama_summary/       Cross-country Excel + summary report

tests/                      pytest test suite (80 tests)
```

---

## CLI Reference

```
pp --help

Commands:
  pp all                   End-to-end pipeline (fetch → validate → run → report)
  pp fetch-data            Pull and cache API data
  pp validate-params       Validate country YAML parameter files
  pp run                   Run calculations; write CSV + Excel tables
  pp build-reports         Generate charts and Markdown reports
  pp build-deep-profiles   Build deep profile JSONs for dashboard
  pp list-countries        List countries with available parameter files
  pp wb-filter-region      List ISO3 codes for a World Bank region (e.g. MEA)
  pp serve                 Launch the Streamlit dashboard locally
```

Common options accepted by most commands:
- `--countries JOR MAR …` – ISO3 codes (or omit to process all available YAMLs)
- `--ref-year 2022`        – Reference year for calculations
- `--config run_config.yaml` – Path to run-config YAML
- `--params-dir data/params` – Override country params directory
- `--output-dir reports/`    – Override report output directory

---

## Outputs Per Country

| File | Description |
|---|---|
| `<ISO3>_results.csv` | Tidy results table (6 earnings multiples × all indicators) |
| `<ISO3>_results.xlsx` | Multi-sheet Excel (Results, Parameters, Component breakdown) |
| `replacement_rates.png` | Gross vs net replacement rates chart |
| `pension_levels.png` | Gross vs net pension levels (% AW) |
| `component_breakdown.png` | Stacked bar by scheme component |
| `pension_wealth.png` | Gross vs net pension wealth (× AW) |
| `<ISO3>_report.md` | Full Markdown (Quarto-compatible) country brief |

Cross-country outputs in `reports/panorama_summary/`:
- `panorama_all_countries.csv`
- `panorama_combined.xlsx` (one sheet per country + Comparative sheet)
- `panorama_summary.md`

---

## Dashboard

The Streamlit dashboard is live at **https://pensions.ramyzeid.com** and runs
locally with:

```bash
pp serve                         # default port 8501
pp serve --port 8502             # custom port
streamlit run pensions_panorama/web/app.py
```

### Dashboard Tabs (9 tabs)

| Tab | Contents |
|---|---|
| 🏠 Database | Cross-country overview table with sortable indicators + NRA global distribution histogram |
| 🌍 Country Profile | Full single-country page with analytics, charts, PDF export, and AI Q&A |
| 📊 Compare | Side-by-side comparison + progressivity chart + cross-country parameter heatmap |
| 📖 Methodology | OECD pension model methodology notes |
| 📋 PAG Tables | Pensions-at-a-Glance style comparative tables |
| 🧮 Pension Calculator | Interactive pension calculator + personal pension projector |
| 💰 Retirement Cost | Retirement cost estimator with HALE-based health split |
| 📖 Glossary | Definitions for all indicators and terms (EN / FR / AR) |
| 🔗 WB Primer Notes | World Bank Pension Reform Primer reference notes |

### Country Profile Layout

The Country Profile tab is a single scrollable page:

1. **Country selector** — flag + name + key metrics (NRA M/F, Gross RR, Avg Wage)
2. **Narrative overview** — auto-generated or hand-curated country text
3. **Country Level Information** — macro + social protection indicators (WDI/ASPIRE/GFDD)
4. **System KPIs** — pension coverage, fund assets, expenditure
5. **Coverage & Adequacy KPIs** — coverage rate, informality, elderly poverty
6. **Gender pension gap** — male vs female GRR at 1×AW
7. **Fiscal sustainability** — RAG signal + scatter vs all peers
8. **Peer benchmarking** — GRR vs nearest income-group peers
9. **Scheme parameter detail** — expandable cards from country YAML
10. **Replacement Rate Sensitivity** — GRR vs service years 5–50, with benefit cap lines
11. **Contributory vs Zero-Contribution Adequacy** — safety-net floor chart
12. **Modeling Results** — OECD-style replacement rate / pension level / wealth table
13. **Charts** — 6 Plotly charts (replacement rates, pension levels, wealth, etc.)
14. **PDF Export** — downloadable country report (schemes, KPIs, indicators, reforms)
15. **Inline Calculators** — pension calculator + retirement cost estimator
16. **Main Pension Schemes** — scheme overview table from deep profile
17. **SSA International Updates** — news feed of recent system changes
18. **Reform Timeline** — visual chronological reform history
19. **AI Q&A** — ask questions about the pension system (powered by Claude Haiku)

### Compare Tab Analytics

Beyond the standard comparison charts, the Compare tab includes:

- **Progressivity chart** — `GRR(0.5×AW) ÷ GRR(2.0×AW)` per country, coloured by income group. Values above 1 indicate the system favours lower earners.
- **Cross-country parameter heatmap** — selectable metric (NRA M/F, employee/employer contribution rate, GRR at 1×AW) across all countries.

### Personal Pension Projector

In the Calculator tab, the projector takes a birth year, starting wage, real wage growth, and contribution density, then estimates:
- Projected wage at NRA
- Gross and net replacement rate
- DC fund accumulation trajectory (if country has a DC pillar)

### Live Data Sync

The sidebar includes a **Refresh live data** button that clears all disk-cached API responses (World Bank, ILO, UN WPP) and Streamlit's data cache, then shows a timestamp. Restart the app to reload fresh values.

### Languages

The dashboard supports **English**, **Français**, and **العربية** (RTL).
All tabs, country names, charts, and glossary content are fully translated.

### AI Q&A

Set the `ANTHROPIC_API_KEY` environment variable to enable the AI Q&A panel at the bottom of every Country Profile. It uses **Claude Haiku** (fast, low-cost) with a country-specific system prompt built from the YAML parameters. Responses are cached for 1 hour per question/country pair.

---

## Bulk YAML Enrichment

The script `scripts/bulk_enrich_yaml.py` enriches all country YAML files in a single run:

```bash
python scripts/bulk_enrich_yaml.py
```

**What it does:**
1. Loops all `data/params/*.yaml` (skips `assumptions.yaml` and `_template.yaml`)
2. Skips files that already have `coverage_rate` (protects hand-curated data for JOR, NOR, POL, GBR, USA, etc.)
3. Fetches `per_si_cp.cov_pop_tot` from the World Bank ASPIRE API and writes a `coverage_rate` block with value, year, and citation
4. Adds `reform_status: stable` to any active scheme that is missing that field
5. Validates each enriched file via Pydantic; restores the original from backup on any validation failure
6. Prints a summary: `Updated N | Skipped N | Errors N`

---

## Deep Profile JSONs

Pre-built JSON files power the Country Profile's narrative, KPI, and scheme
overview sections. They are committed to the repo under `reports/deep_profiles/`
and rebuilt with:

```bash
# All 189 countries (live API data)
pp build-deep-profiles

# Specific countries
pp build-deep-profiles --countries "CRI JOR MAR"

# Offline (no network calls; uses cached data + mapping overrides only)
pp build-deep-profiles --offline
```

### What Each JSON Contains

- **Narrative** — auto-generated from YAML params or hand-written in the mapping file
- **Country Level Information** — 7 indicators fetched live:
  - GDP per capita (LCU and USD) — World Bank WDI
  - Population age 65+ (count and %) — World Bank WDI
  - Contributory pension coverage (% of population) — ASPIRE
  - Social insurance coverage (% of population) — ASPIRE
  - Pension fund assets (% of GDP) — GFDD
- **System KPIs** — auto-filled from ASPIRE/GFDD where available
- **Schemes** — auto-generated from YAML params or hand-curated in mapping file

> **Data availability note**: ASPIRE indicators are derived from household surveys
> and are strongest for LMICs (~100 countries). Most high-income/OECD countries
> return "Not available" — this is expected and displays cleanly in the dashboard.

### Scheme Mapping Files

Per-country overrides live in `data/deep_profiles/<ISO3>.yaml`. Each file can define:
- `narrative` — hand-written text + sources
- `system_kpis` — manual values that override ASPIRE/GFDD auto-fill
- `country_indicators` — overrides for Country Level Information
- `schemes` — hand-curated scheme attributes (members, contributors, revenues, etc.)

Start from `data/deep_profiles/_template.yaml`. Missing values display as
**Not available** but the rows remain visible.

---

## Current Status (Feb 27, 2026)

- **Live at https://pensions.ramyzeid.com** — deployed on Streamlit Community Cloud,
  domain on Cloudflare, auto-deploys on every `git push` to `main`.
- **9-tab dashboard** with 10 new analytics features (v2.0).
- **3 languages** — English, French, Arabic (RTL) across all tabs including Glossary.
- **189 countries** — YAML pension parameter files and deep profile JSONs for all
  World Bank member countries.
- **ASPIRE + GFDD data live** — Contributory pension coverage, social insurance
  coverage, and pension fund assets/GDP auto-fetched and displayed per country.
- **Tab persistence** — `@st.fragment` on all tab functions; selecting a country or
  changing a widget does not reset the active tab.
- **Offline mode** — `--offline` skips all network calls; useful for CI builds.
- **Tests** — 80 tests passing.

### New in v2.0 (Feb 27, 2026)

| Feature | Where |
|---|---|
| **Replacement Rate Sensitivity** | Country Profile — GRR vs service years, with min/max benefit cap lines |
| **Adequacy Gap chart** | Country Profile — full-career vs zero-contribution comparison |
| **PDF Country Report** | Country Profile — downloadable PDF (schemes, KPIs, indicators, reforms) |
| **AI Q&A** | Country Profile — Claude Haiku answers questions with country context |
| **Progressivity chart** | Compare tab — GRR(0.5×AW) ÷ GRR(2.0×AW) per country |
| **Parameter Heatmap** | Compare tab — selectable metric across all countries |
| **NRA Distribution** | Overview tab — histogram of male NRA by income group |
| **Personal Projector** | Calculator tab — birth year → projected pension + DC trajectory |
| **Live Data Sync** | Sidebar — clears all API caches and timestamps the refresh |
| **Bulk YAML Enrichment** | `scripts/bulk_enrich_yaml.py` — WB coverage_rate + reform_status |

---

## Result Indicators

For each earnings multiple (0.5 / 0.75 / 1.0 / 1.5 / 2.0 / 2.5 × AW):

| Indicator | Definition |
|---|---|
| Gross pension level | Annual gross pension ÷ annual average wage |
| Net pension level | Annual net pension ÷ annual average wage |
| Gross replacement rate | Annual gross pension ÷ individual pre-retirement wage |
| Net replacement rate | Annual net pension ÷ individual pre-retirement wage |
| Gross pension wealth | PV of gross benefit stream ÷ average wage |
| Net pension wealth | PV of net benefit stream ÷ average wage |

Pension wealth uses survival-weighted discounting from UN WPP life tables
where available; falls back to a simplified annuity formula otherwise.

---

## Data Sources and Provenance

| Source | Purpose | Indicators |
|---|---|---|
| **Human-curated YAML** | Pension rules, benefit formulas, contribution rates | `data/params/<ISO3>.yaml` |
| **ILOSTAT SDMX API** | Average earnings (preferred source) | `EAR_4MTH_SEX_ECO_CUR_NB_A` |
| **World Bank WDI API** | GDP per capita, population 65+, macro context | `NY.GDP.PCAP.*`, `SP.POP.*` |
| **World Bank ASPIRE** | Pension and social insurance coverage | `per_si_cp.cov_pop_tot`, `per_si_allsi.cov_pop_tot` |
| **World Bank GFDD** | Pension fund assets as % of GDP | `GFDD.DI.13` |
| **UN WPP Data Portal** | Life tables for pension-wealth calculation | Indicators 28 (lx), 75 (ex) |

All sources share the same `WorldBankClient` (WDI v2 REST API). Responses are
cached on disk under `data/raw/cache/` with configurable TTL (default 7 days;
UN data 30 days). Use the **Refresh live data** button in the sidebar, or delete
the cache directory, to force a fresh pull.

---

## Modeling Assumptions

Global assumptions are in `data/params/assumptions.yaml`. Key defaults:

| Parameter | Default | OECD benchmark |
|---|---|---|
| Entry age | 20 | 20 |
| Career length | 40 years | 40 years |
| Contribution density | 100% | 100% |
| Real wage growth | 2%/yr | 2%/yr |
| Discount rate | 2% real | 2% real |
| DC net real return | 3%/yr | 3%/yr |
| WPP life table year | 2020 | varies |

---

## How to Add a New Country

1. **Copy the template**
   ```bash
   cp data/params/_template.yaml data/params/EGY.yaml
   ```

2. **Fill in all fields** — every `value` field must have a `source_citation`.
   Key fields to research:
   - `eligibility.normal_retirement_age_male/female`
   - `contributions.employee_rate` and `employer_rate`
   - `benefits.accrual_rate_per_year` (for DB) or `flat_rate_aw_multiple` (for basic)
   - `benefits.minimum_benefit_aw_multiple` / `maximum_benefit_aw_multiple`
   - `average_earnings.manual_value` or ILOSTAT series ID
   - `taxes.simplified_net_rate`

3. **Validate**
   ```bash
   pp validate-params --countries EGY
   ```

4. **Run**
   ```bash
   pp all --countries EGY --ref-year 2022
   ```

5. **Build deep profile**
   ```bash
   pp build-deep-profiles --countries EGY
   ```

6. **Commit** the YAML and JSON files with citation history in `sources`.

---

## Running the Tests

```bash
pytest tests/ -v
```

The test suite includes:
- **Schema validation** — valid YAMLs load; invalid ones are rejected
- **Pension engine unit tests** — DB formula, basic, minimum guarantee, NDC, DC
- **Tax engine tests** — flat rate and progressive bracket engine
- **Pension wealth math** — annuity factor formulas and edge cases
- **World Bank client** — mocked HTTP responses with `responses` library
- **End-to-end** — Jordan and Morocco with fixed assumptions

---

## Extending the Model

### Adding a country-specific tax module

Create `pensions_panorama/countries/EGY_tax.py`:

```python
from pensions_panorama.model.tax_engine import BracketTaxEngine, TaxEngineBase

def get_tax_engine(avg_wage: float) -> TaxEngineBase:
    # Egyptian income tax brackets (2023, EGP)
    return BracketTaxEngine(
        brackets=[
            (15_000, 0.00),
            (30_000, 0.10),
            (45_000, 0.15),
            (60_000, 0.20),
            (200_000, 0.225),
            (400_000, 0.25),
            (float("inf"), 0.275),
        ],
        basic_allowance=9_000,
        social_contrib_rate=0.0,
        average_wage=avg_wage,
    )
```

Then call `get_tax_engine()` in a custom `PensionEngine` subclass that overrides
`_apply_tax()`.

### Adding a points or NDC scheme

Set `type: "points"` or `type: "NDC"` in the YAML, and fill the appropriate
benefit fields (`point_value`, `notional_interest_rate`, `annuity_divisor_at_nra`).
The engine dispatches automatically.

---

## Dependencies

Pinned in `pyproject.toml`. Key libraries:

- `pydantic>=2.5` — YAML schema validation
- `typer` — CLI
- `streamlit` — dashboard
- `plotly` — interactive charts
- `requests` + `tenacity` — API calls with retries
- `diskcache` — disk-based caching
- `pandas` + `pyarrow` — data processing
- `matplotlib` — static charts
- `jinja2` — report templates
- `openpyxl` — Excel export
- `anthropic>=0.30` — AI Q&A via Claude Haiku (requires `ANTHROPIC_API_KEY`)
- `fpdf2>=2.7` — PDF country report generation
- `kaleido>=0.2` — Plotly static image export for PDF charts
