# Pensions Panorama

A production-quality, reproducible Python project that generates
**Pensions-at-a-Glance**-style comparative datasets and country briefs
for a user-specified set of countries.

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
│   ├── worldbank.py        World Bank Indicators API client
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

data/
├── params/
│   ├── assumptions.yaml    Global modeling assumptions
│   ├── _template.yaml      Blank country template (start here)
│   ├── JOR.yaml            Jordan (sample)
│   └── MAR.yaml            Morocco (sample)
├── raw/cache/              Disk-cached API responses (timestamped)
└── processed/              Cleaned datasets in Parquet

reports/
├── country/<ISO3>/         One folder per country (CSV, Excel, charts, .md)
└── panorama_summary/       Cross-country Excel + summary report

tests/                      pytest test suite
```

---

## CLI Reference

```
pp --help

Commands:
  pp all               End-to-end pipeline (fetch → validate → run → report)
  pp fetch-data        Pull and cache API data
  pp validate-params   Validate country YAML parameter files
  pp run               Run calculations; write CSV + Excel tables
  pp build-reports     Generate charts and Markdown reports
  pp list-countries    List countries with available parameter files
  pp wb-filter-region  List ISO3 codes for a World Bank region (e.g. MEA)
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

## Deep Profile (Dashboard)

The Streamlit dashboard includes a **Country Deep Profile** tab powered by
build-time JSON outputs under:

```
reports/deep_profiles/<ISO3>.json
```

Build them with:

```bash
pp build-deep-profiles --countries CRI
```

If you are offline or the World Bank API is unreachable, use:

```bash
pp build-deep-profiles --countries CRI --offline
```

### Current Status (Feb 26, 2026)

Work completed:
- **Country YAML params**: All 189 World Bank member countries have YAML pension
  parameter files under `data/params/`.
- **All 189 deep profile JSONs built**: `reports/deep_profiles/<ISO3>.json` exists
  for every country; run `pp build-deep-profiles` to refresh with latest WDI data.
- **Country Deep Profile tab**: Streamlit dashboard tab is live at
  `http://localhost:8501` (run `pp serve` or `streamlit run pensions_panorama/web/app.py`).
- **Deep profile schema + builder + CLI**: `pp build-deep-profiles` generates
  `reports/deep_profiles/<ISO3>.json` for every country.
- **Auto-enrichment from params**: Countries without a hand-written mapping file
  auto-populate scheme attributes (contribution rates, retirement ages, benefit type,
  financing mechanism) directly from their `data/params/<ISO3>.yaml`.
- **Live WDI data**: GDP per capita (LCU/USD), population 65+, and ASPIRE coverage
  KPIs are fetched from the World Bank WDI API and cached locally.
- **Country selection sync**: The Deep Profile tab defaults to whichever country is
  selected in the Country Profile tab.
- **Tab persistence**: All 10 dashboard tabs are decorated with `@st.fragment` so that
  selecting a country (or changing any widget) within a tab no longer resets the active
  tab back to Panorama. Only the affected tab's fragment re-runs; the tab bar is
  untouched.
- **Offline mode**: `--offline` skips all network calls; useful for CI or air-gapped builds.
- **Enriched mapping files**: `CRI`, `JOR`, `MAR` have hand-curated narratives and
  scheme data sourced from OECD Pensions at a Glance and ILO.
- **Compact number formatting**: Large LCU values displayed as `M`/`B` suffixes.
- **Tests**: 80 tests passing (ordering, auto-enrichment, structure, not-available,
  fallback narrative, scheme type group detection).

### Running the dashboard

```bash
pp serve                         # default port 8501
pp serve --port 8502             # custom port
streamlit run pensions_panorama/web/app.py
```

Open **http://localhost:8501** in your browser.

### Building / refreshing deep profiles

```bash
# All 189 countries (live WDI data)
pp build-deep-profiles

# Specific countries
pp build-deep-profiles --countries "CRI JOR MAR"

# Offline (no network calls; uses cached data + mapping overrides only)
pp build-deep-profiles --offline
```

### Next Steps

1. **Expand hand-curated mappings**: Add richer scheme-level statistics (members,
   contributors, beneficiaries, revenues as % of GDP) for more countries by creating
   or extending `data/deep_profiles/<ISO3>.yaml` from the template.
2. **ASPIRE KPIs**: Wire up ASPIRE social protection indicators for coverage KPIs
   where WDI does not carry them (many LIC/LMIC countries).
3. **Narrative quality**: Replace the auto-generated fallback narrative with
   hand-written text for high-priority countries (add `narrative.text` in the
   mapping YAML).

### Scheme Mapping Files

Per-country scheme mappings live in:

```
data/deep_profiles/<ISO3>.yaml
```

Each file defines:
- `narrative` text and sources
- `system_kpis` (coverage, spending, etc.)
- `country_indicators` overrides for Country Level Information (optional)
- `schemes` with `scheme_type_group` ordering (`noncontrib`, `dc`, `db`)
- per-scheme attributes and sources

Start from:

```
data/deep_profiles/_template.yaml
```

If values are missing, the UI will display **Not available** but keep the rows
visible.

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

## How to Add a New Country

1. **Copy the template**
   ```bash
   cp data/params/_template.yaml data/params/EGY.yaml
   ```

2. **Fill in all fields** – every `value` field must have a `source_citation`.
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

5. **Commit** the YAML file with the citation history in `sources`.

---

## Data Sources and Provenance

| Source | Purpose | Client |
|---|---|---|
| **Human-curated YAML** | Pension rules, benefit formulas, contribution rates | `schema/params_schema.py` |
| **ILOSTAT SDMX API** | Average earnings (preferred) | `sources/ilostat_sdmx.py` |
| **World Bank Indicators API** | Macro context: CPI, GDP, population | `sources/worldbank.py` |
| **UN WPP Data Portal API** | Life tables for pension-wealth calculation | `sources/un_dataportal.py` |

**Caching**: All API responses are cached on disk under `data/raw/cache/`
with configurable TTL (default 7 days; UN data 30 days).  Set `cache_ttl_days`
in `run_config.yaml` to control.  Delete the cache directory to force a fresh pull.

**Reproducibility**: Given the same `run_config.yaml`, the same `data/params/`
YAML files, and the same cached API responses, every run produces bit-identical outputs.

---

## Modeling Assumptions

Global assumptions are in `data/params/assumptions.yaml`.  Key defaults:

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

## Running the Tests

```bash
pytest tests/ -v
```

The test suite includes:
- **Schema validation** – valid YAMLs load; invalid ones are rejected
- **Pension engine unit tests** – DB formula, basic, minimum guarantee, NDC, DC
- **Tax engine tests** – flat rate and progressive bracket engine
- **Pension wealth math** – annuity factor formulas and edge cases
- **World Bank client** – mocked HTTP responses with `responses` library
- **End-to-end** – Jordan and Morocco with fixed assumptions

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

Pinned in `pyproject.toml`.  Key libraries:

- `pydantic>=2.5` – YAML schema validation
- `typer` – CLI
- `requests` + `tenacity` – API calls with retries
- `diskcache` – disk-based caching
- `pandas` + `pyarrow` – data processing
- `matplotlib` – charts
- `jinja2` – report templates
- `openpyxl` – Excel export
