"""Pensions Panorama CLI.

Commands
--------
pp fetch-data   – Pull and cache API data (World Bank, UN, ILOSTAT)
pp validate-params – Validate country YAML parameter files
pp run          – Run pension calculations for one or more countries
pp build-reports – Generate charts, tables, and markdown reports
pp all          – End-to-end pipeline (fetch → validate → run → report)
pp list-countries – List countries with validated parameter files

Usage example
-------------
pp all --countries JOR MAR --ref-year 2022
pp run --countries JOR --ref-year 2022 --output-dir /tmp/out
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Annotated, Optional

import typer
import yaml
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    name="pp",
    help="Pensions Panorama – comparative pension dataset and country briefs.",
    add_completion=False,
)
console = Console()

# ---------------------------------------------------------------------------
# Common option types
# ---------------------------------------------------------------------------
CountriesArg = Annotated[
    Optional[list[str]],
    typer.Option(
        "--countries", "-c",
        help="Space-separated ISO3 codes, or omit to process all available param files.",
    ),
]
RefYearOpt = Annotated[
    int,
    typer.Option("--ref-year", "-y", help="Reference year for calculations."),
]
StartYearOpt = Annotated[int, typer.Option("--start-year", help="Earliest API data year.")]
EndYearOpt = Annotated[int, typer.Option("--end-year", help="Latest API data year.")]
ConfigOpt = Annotated[
    Optional[Path],
    typer.Option("--config", help="Path to run-config YAML (overrides defaults)."),
]
ParamsDirOpt = Annotated[
    Optional[Path],
    typer.Option("--params-dir", help="Directory containing country YAML files."),
]
OutputDirOpt = Annotated[
    Optional[Path],
    typer.Option("--output-dir", "-o", help="Root output directory for reports."),
]
SexOpt = Annotated[str, typer.Option("--sex", help="Modeled sex: male | female | total.")]
OfflineOpt = Annotated[
    bool, typer.Option("--offline", help="Skip network calls; use cached/overrides only.")
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_cfg(config: Path | None, overrides: dict | None = None):
    from pensions_panorama.config import load_run_config, setup_logging
    cfg = load_run_config(config)
    if overrides:
        for k, v in overrides.items():
            if v is not None:
                object.__setattr__(cfg, k, v)
    setup_logging(cfg.log_level)
    return cfg


def _resolve_countries(
    countries: list[str] | None,
    params_dir: Path,
) -> list[str]:
    """Return ISO3 list: explicit list or all YAML files in params_dir."""
    if countries:
        if len(countries) == 1:
            raw = countries[0]
            if "," in raw or " " in raw:
                parts = [p for p in raw.replace(",", " ").split() if p]
                return [p.upper() for p in parts]
        return [c.upper() for c in countries]
    yamls = list(params_dir.glob("*.yaml")) + list(params_dir.glob("*.yml"))
    resolved = [
        p.stem.upper()
        for p in yamls
        if not p.stem.startswith("_") and p.stem.lower() != "assumptions"
    ]
    if not resolved:
        console.print("[yellow]No country param files found in %s[/]" % params_dir)
    return resolved


def _load_params(iso3: str, params_dir: Path):
    from pensions_panorama.schema.params_schema import load_country_params
    candidates = [
        params_dir / f"{iso3}.yaml",
        params_dir / f"{iso3.lower()}.yaml",
    ]
    for p in candidates:
        if p.exists():
            return load_country_params(p)
    raise FileNotFoundError(f"No param file found for {iso3} in {params_dir}")


def _resolve_average_wage(params, cfg, ref_year: int) -> float:
    """Pull average wage from ILOSTAT or fall back to manual value."""
    from pensions_panorama.sources.ilostat_sdmx import ILOStatClient
    ae = params.average_earnings

    ilo = ILOStatClient(cache_ttl_seconds=cfg.cache_ttl_seconds)
    if ae.ilostat_series_id:
        val = ilo.get_average_annual_earnings(
            iso3=params.metadata.iso3,
            ref_year=ref_year,
            indicator=ae.ilostat_series_id,
            transformation=ae.ilostat_transformation,
        )
        if val is not None:
            return val
        console.print(
            f"[yellow]  ILOSTAT data unavailable for {params.metadata.iso3}; "
            "falling back to manual value.[/]"
        )

    if ae.manual_value is not None:
        return float(ae.manual_value)

    raise RuntimeError(
        f"No average wage available for {params.metadata.iso3}. "
        "Set manual_value in the YAML or provide an ILOSTAT series ID."
    )


# ---------------------------------------------------------------------------
# fetch-data
# ---------------------------------------------------------------------------

@app.command("fetch-data")
def fetch_data(
    countries: CountriesArg = None,
    start_year: StartYearOpt = 2010,
    end_year: EndYearOpt = 2023,
    config: ConfigOpt = None,
    params_dir: ParamsDirOpt = None,
) -> None:
    """Pull and cache API data from World Bank, UN, and ILOSTAT."""
    from pensions_panorama.config import PARAMS_DIR
    from pensions_panorama.sources.worldbank import WorldBankClient
    from pensions_panorama.sources.un_dataportal import UNDataPortalClient
    from pensions_panorama.sources.ilostat_sdmx import ILOStatClient

    cfg = _load_cfg(config)
    pd = params_dir or cfg.resolved_params_dir
    iso3_list = _resolve_countries(countries, pd)

    if not iso3_list:
        console.print("[red]No countries specified.[/]")
        raise typer.Exit(1)

    console.print(f"[bold]Fetching data for: {', '.join(iso3_list)}[/]")
    wb = WorldBankClient(cache_ttl_seconds=cfg.cache_ttl_seconds)
    un = UNDataPortalClient(cache_ttl_seconds=cfg.cache_ttl_seconds * 4)
    ilo = ILOStatClient(cache_ttl_seconds=cfg.cache_ttl_seconds)

    for iso3 in iso3_list:
        console.print(f"  [cyan]{iso3}[/] – World Bank macro indicators...")
        wb.fetch_macro_context(iso3, start_year, end_year)

        console.print(f"  [cyan]{iso3}[/] – UN life tables...")
        try:
            params_obj = _load_params(iso3, pd)
            un_loc = params_obj.metadata.un_location_id or un.get_location_id(iso3)
            if un_loc:
                un.get_life_table(iso3, cfg.ref_year - (cfg.ref_year % 5), "male")
                un.get_life_table(iso3, cfg.ref_year - (cfg.ref_year % 5), "female")
        except (FileNotFoundError, Exception) as e:
            console.print(f"    [yellow]UN/params issue for {iso3}: {e}[/]")

        console.print(f"  [cyan]{iso3}[/] – ILOSTAT earnings...")
        try:
            params_obj = _load_params(iso3, pd)
            ae = params_obj.average_earnings
            if ae.ilostat_series_id:
                ilo.fetch_earnings_series(iso3, ae.ilostat_series_id,
                                          start_year=start_year, end_year=end_year)
        except (FileNotFoundError, Exception) as e:
            console.print(f"    [yellow]ILOSTAT issue for {iso3}: {e}[/]")

    console.print("[green]Data fetch complete.[/]")


# ---------------------------------------------------------------------------
# validate-params
# ---------------------------------------------------------------------------

@app.command("validate-params")
def validate_params(
    countries: CountriesArg = None,
    params_dir: ParamsDirOpt = None,
    config: ConfigOpt = None,
) -> None:
    """Validate country YAML parameter files against the Pydantic schema."""
    from pensions_panorama.config import PARAMS_DIR

    cfg = _load_cfg(config)
    pd_path = params_dir or cfg.resolved_params_dir
    iso3_list = _resolve_countries(countries, pd_path)

    if not iso3_list:
        console.print("[red]No countries specified.[/]")
        raise typer.Exit(1)

    table = Table(title="Parameter Validation Results")
    table.add_column("ISO3", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Detail")

    all_ok = True
    for iso3 in iso3_list:
        try:
            params = _load_params(iso3, pd_path)
            table.add_row(iso3, "[green]OK[/]",
                          f"{len(params.schemes)} scheme(s) validated.")
        except FileNotFoundError as e:
            table.add_row(iso3, "[yellow]MISSING[/]", str(e))
            all_ok = False
        except Exception as e:
            table.add_row(iso3, "[red]ERROR[/]", str(e)[:120])
            all_ok = False

    console.print(table)
    if not all_ok:
        raise typer.Exit(1)


# ---------------------------------------------------------------------------
# run
# ---------------------------------------------------------------------------

@app.command("run")
def run(
    countries: CountriesArg = None,
    ref_year: RefYearOpt = 2023,
    config: ConfigOpt = None,
    params_dir: ParamsDirOpt = None,
    output_dir: OutputDirOpt = None,
    sex: SexOpt = "male",
) -> None:
    """Run pension calculations and save result tables (CSV + Excel)."""
    from pensions_panorama.config import PARAMS_DIR, PANORAMA_DIR
    from pensions_panorama.model.assumptions import load_assumptions
    from pensions_panorama.model.pension_engine import PensionEngine
    from pensions_panorama.model.pension_wealth import PensionWealthCalculator
    from pensions_panorama.sources.un_dataportal import UNDataPortalClient
    from pensions_panorama.reporting.export import (
        export_country_csv, export_country_excel,
        export_panorama_csv, export_panorama_excel,
        results_to_df,
    )

    cfg = _load_cfg(config, {"ref_year": ref_year, "sex": sex})
    pd_path = params_dir or cfg.resolved_params_dir
    out_root = output_dir or cfg.resolved_reports_dir
    iso3_list = _resolve_countries(countries, pd_path)

    if not iso3_list:
        console.print("[red]No countries specified.[/]")
        raise typer.Exit(1)

    assumptions = load_assumptions(cfg.assumptions_file, pd_path)
    un_client = UNDataPortalClient(cache_ttl_seconds=cfg.cache_ttl_seconds * 4)

    all_dfs: dict[str, "pd.DataFrame"] = {}
    errors: list[str] = []

    for iso3 in iso3_list:
        console.print(f"[bold cyan]Running {iso3}...[/]")
        try:
            params = _load_params(iso3, pd_path)
            avg_wage = _resolve_average_wage(params, cfg, ref_year)
            console.print(f"  Average wage: {params.metadata.currency_code} {avg_wage:,.0f}")

            # Survival-weighted annuity factor
            pw_calc = PensionWealthCalculator(assumptions, iso3, un_client)
            wpp_year = assumptions.wpp_year
            survival_factor = pw_calc.annuity_factor(sex=sex)
            console.print(f"  Annuity factor ({sex}): {survival_factor:.4f}")

            engine = PensionEngine(
                country_params=params,
                assumptions=assumptions,
                average_wage=avg_wage,
                survival_factor=survival_factor,
            )
            results = engine.run_all_multiples(cfg.earnings_multiples, sex=sex)

            # Country output directory
            country_dir = out_root / "country" / iso3
            country_dir.mkdir(parents=True, exist_ok=True)

            export_country_csv(results, iso3, params.metadata.country_name, country_dir)
            export_country_excel(results, iso3, params.metadata.country_name, params, country_dir)

            df = results_to_df(results, iso3, params.metadata.country_name)
            all_dfs[iso3] = df
            console.print(f"  [green]Done.[/] Results in {country_dir}")

        except Exception as e:
            console.print(f"  [red]ERROR: {e}[/]")
            errors.append(f"{iso3}: {e}")
            logging.getLogger(__name__).exception("Error running %s", iso3)

    # Panorama outputs
    panorama_dir = out_root / "panorama_summary"
    panorama_dir.mkdir(parents=True, exist_ok=True)
    if all_dfs:
        export_panorama_csv(all_dfs, panorama_dir)
        export_panorama_excel(all_dfs, panorama_dir)
        console.print(f"[green]Panorama outputs written to {panorama_dir}[/]")

    if errors:
        console.print(f"[red]{len(errors)} error(s) occurred:[/]")
        for e in errors:
            console.print(f"  - {e}")
        raise typer.Exit(1)


# ---------------------------------------------------------------------------
# build-reports
# ---------------------------------------------------------------------------

@app.command("build-reports")
def build_reports(
    countries: CountriesArg = None,
    ref_year: RefYearOpt = 2023,
    config: ConfigOpt = None,
    params_dir: ParamsDirOpt = None,
    output_dir: OutputDirOpt = None,
    sex: SexOpt = "male",
) -> None:
    """Generate charts and markdown reports (requires run to have completed first)."""
    from pensions_panorama.config import PARAMS_DIR
    from pensions_panorama.model.assumptions import load_assumptions
    from pensions_panorama.model.pension_engine import PensionEngine
    from pensions_panorama.model.pension_wealth import PensionWealthCalculator
    from pensions_panorama.sources.un_dataportal import UNDataPortalClient
    from pensions_panorama.sources.worldbank import WorldBankClient
    from pensions_panorama.reporting.charts import generate_all_charts
    from pensions_panorama.reporting.country_report import (
        generate_country_report, generate_panorama_summary,
    )
    from pensions_panorama.reporting.export import results_to_df

    cfg = _load_cfg(config, {"ref_year": ref_year, "sex": sex})
    pd_path = params_dir or cfg.resolved_params_dir
    out_root = output_dir or cfg.resolved_reports_dir
    iso3_list = _resolve_countries(countries, pd_path)

    assumptions = load_assumptions(cfg.assumptions_file, pd_path)
    un_client = UNDataPortalClient(cache_ttl_seconds=cfg.cache_ttl_seconds * 4)
    wb_client = WorldBankClient(cache_ttl_seconds=cfg.cache_ttl_seconds)

    all_country_results: dict = {}
    errors: list[str] = []

    for iso3 in iso3_list:
        console.print(f"[bold cyan]Building report for {iso3}...[/]")
        try:
            params = _load_params(iso3, pd_path)
            avg_wage = _resolve_average_wage(params, cfg, ref_year)

            pw_calc = PensionWealthCalculator(assumptions, iso3, un_client)
            survival_factor = pw_calc.annuity_factor(sex=sex)

            engine = PensionEngine(
                country_params=params,
                assumptions=assumptions,
                average_wage=avg_wage,
                survival_factor=survival_factor,
            )
            results = engine.run_all_multiples(cfg.earnings_multiples, sex=sex)

            country_dir = out_root / "country" / iso3
            country_dir.mkdir(parents=True, exist_ok=True)

            # Charts
            chart_paths = generate_all_charts(
                results, params.metadata.country_name, country_dir
            )

            # Macro context
            macro_df = None
            try:
                macro_df = wb_client.fetch_macro_context(iso3, cfg.start_year, ref_year)
            except Exception:
                pass

            # Markdown report
            generate_country_report(
                params=params,
                results=results,
                assumptions=assumptions,
                average_wage=avg_wage,
                out_dir=country_dir,
                chart_paths=chart_paths,
                macro_df=macro_df,
            )
            all_country_results[iso3] = (params, results)
            console.print(f"  [green]Done.[/] Reports in {country_dir}")

        except Exception as e:
            console.print(f"  [red]ERROR: {e}[/]")
            errors.append(f"{iso3}: {e}")
            logging.getLogger(__name__).exception("Error building report for %s", iso3)

    # Panorama summary report
    if all_country_results:
        panorama_dir = out_root / "panorama_summary"
        generate_panorama_summary(all_country_results, panorama_dir)
        console.print(f"[green]Panorama summary written to {panorama_dir}[/]")

    if errors:
        console.print(f"[red]{len(errors)} error(s).[/]")
        raise typer.Exit(1)


# ---------------------------------------------------------------------------
# build-deep-profiles
# ---------------------------------------------------------------------------

@app.command("build-deep-profiles")
def build_deep_profiles(
    countries: CountriesArg = None,
    config: ConfigOpt = None,
    params_dir: ParamsDirOpt = None,
    output_dir: OutputDirOpt = None,
    ref_year: RefYearOpt = 2023,
    offline: OfflineOpt = False,
) -> None:
    """Generate deep profile JSON outputs for the dashboard."""
    from pensions_panorama.deep_profile.builder import build_deep_profile, write_deep_profile
    from pensions_panorama.sources.worldbank import WorldBankClient

    cfg = _load_cfg(config, {"ref_year": ref_year})
    pd_path = params_dir or cfg.resolved_params_dir
    out_root = output_dir or cfg.resolved_reports_dir
    iso3_list = _resolve_countries(countries, pd_path)

    wb_client = WorldBankClient(cache_ttl_seconds=cfg.cache_ttl_seconds)

    for iso3 in iso3_list:
        console.print(f"[bold cyan]Building deep profile for {iso3}...[/]")
        try:
            params = _load_params(iso3, pd_path)
            profile = build_deep_profile(iso3, params, cfg, wb_client, offline=offline)
            out_dir = out_root / "deep_profiles"
            path = write_deep_profile(profile, out_dir)
            console.print(f"  [green]Done.[/] {path}")
        except Exception as e:
            console.print(f"  [red]ERROR: {e}[/]")
            logging.getLogger(__name__).exception("Error building deep profile for %s", iso3)


# ---------------------------------------------------------------------------
# all (end-to-end)
# ---------------------------------------------------------------------------

@app.command("all")
def run_all(
    countries: CountriesArg = None,
    ref_year: RefYearOpt = 2023,
    start_year: StartYearOpt = 2010,
    end_year: EndYearOpt = 2023,
    config: ConfigOpt = None,
    params_dir: ParamsDirOpt = None,
    output_dir: OutputDirOpt = None,
    sex: SexOpt = "male",
) -> None:
    """End-to-end pipeline: fetch → validate → run → build-reports → deep-profiles."""
    console.print("[bold]Running end-to-end Pensions Panorama pipeline...[/]")

    ctx = typer.Context(run_all)

    # Delegate to each sub-command in order
    validate_params(countries=countries, params_dir=params_dir, config=config)
    fetch_data(countries=countries, start_year=start_year, end_year=end_year,
               config=config, params_dir=params_dir)
    run(countries=countries, ref_year=ref_year, config=config,
        params_dir=params_dir, output_dir=output_dir, sex=sex)
    build_reports(countries=countries, ref_year=ref_year, config=config,
                  params_dir=params_dir, output_dir=output_dir, sex=sex)
    build_deep_profiles(countries=countries, ref_year=ref_year, config=config,
                        params_dir=params_dir, output_dir=output_dir)

    console.print("[bold green]Pipeline complete.[/]")


# ---------------------------------------------------------------------------
# list-countries
# ---------------------------------------------------------------------------

@app.command("list-countries")
def list_countries(
    params_dir: ParamsDirOpt = None,
    config: ConfigOpt = None,
    region: Annotated[Optional[str], typer.Option("--region", help="WB region code")] = None,
) -> None:
    """List countries with available parameter files."""
    from pensions_panorama.config import PARAMS_DIR

    cfg = _load_cfg(config)
    pd_path = params_dir or cfg.resolved_params_dir
    iso3_list = _resolve_countries(None, pd_path)

    table = Table(title=f"Countries in {pd_path}")
    table.add_column("ISO3", style="cyan")
    table.add_column("Country Name")
    table.add_column("Schemes")
    table.add_column("Reference Year")

    for iso3 in sorted(iso3_list):
        try:
            params = _load_params(iso3, pd_path)
            if region and (params.metadata.wb_region or "").upper() != region.upper():
                continue
            table.add_row(
                iso3,
                params.metadata.country_name,
                str(len(params.schemes)),
                str(params.metadata.reference_year),
            )
        except Exception as e:
            table.add_row(iso3, f"[red]Error: {e}[/]", "—", "—")

    console.print(table)


# ---------------------------------------------------------------------------
# wb-filter-region  (helper to find country codes)
# ---------------------------------------------------------------------------

@app.command("wb-filter-region")
def wb_filter_region(
    region: Annotated[str, typer.Argument(help="WB region code e.g. 'MEA'")],
    config: ConfigOpt = None,
) -> None:
    """List ISO3 codes for all World Bank countries in a region."""
    from pensions_panorama.sources.worldbank import WorldBankClient

    cfg = _load_cfg(config)
    wb = WorldBankClient(cache_ttl_seconds=cfg.cache_ttl_seconds)
    codes = wb.filter_countries_by_region(region)
    if codes:
        console.print(f"Countries in WB region [cyan]{region}[/]:")
        console.print("  " + "  ".join(codes))
    else:
        console.print(f"[yellow]No countries found for region '{region}'.[/]")


# ---------------------------------------------------------------------------
# serve  (Streamlit dashboard)
# ---------------------------------------------------------------------------

@app.command("serve")
def serve(
    port: Annotated[int, typer.Option("--port", "-p", help="Port to run on.")] = 8501,
    config: ConfigOpt = None,
) -> None:
    """Launch the interactive Streamlit web dashboard."""
    import subprocess
    import sys
    from pathlib import Path

    app_path = Path(__file__).parent / "web" / "app.py"
    if not app_path.exists():
        console.print(f"[red]Web app not found at {app_path}[/]")
        raise typer.Exit(1)

    console.print(f"[bold green]Starting Pensions Panorama dashboard on port {port}…[/]")
    console.print(f"  Open [cyan]http://localhost:{port}[/] in your browser.")
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", str(app_path),
         "--server.port", str(port), "--server.headless", "false"],
        check=False,
    )


# ---------------------------------------------------------------------------
# calc  (personalised pension calculator)
# ---------------------------------------------------------------------------

@app.command("calc")
def calc(
    country: Annotated[str, typer.Option("--country", "-C", help="ISO3 country code.")] = "JOR",
    worker_type: Annotated[
        str, typer.Option("--worker-type", "-w", help="Worker type ID (e.g. private_employee).")
    ] = "private_employee",
    sex: SexOpt = "male",
    age: Annotated[float, typer.Option("--age", help="Current age (years).")] = 60.0,
    service_years: Annotated[
        float, typer.Option("--service-years", help="Years of contributions / service.")
    ] = 25.0,
    wage: Annotated[float, typer.Option("--wage", help="Annual wage in wage-unit.")] = 0.0,
    wage_unit: Annotated[
        str, typer.Option("--wage-unit", help="'currency' or 'aw_multiple'.")
    ] = "currency",
    ref_year: RefYearOpt = 2023,
    config: ConfigOpt = None,
    params_dir: ParamsDirOpt = None,
    output: Annotated[
        str, typer.Option("--output", "-f", help="Output format: 'text' or 'json'.")
    ] = "text",
) -> None:
    """Compute a personalised pension benefit for one person."""
    from pensions_panorama.config import PARAMS_DIR
    from pensions_panorama.model.assumptions import load_assumptions
    from pensions_panorama.model.pension_engine import PensionEngine
    from pensions_panorama.model.pension_wealth import PensionWealthCalculator
    from pensions_panorama.model.calculator import PersonProfile
    from pensions_panorama.sources.un_dataportal import UNDataPortalClient
    import dataclasses

    cfg = _load_cfg(config, {"ref_year": ref_year, "sex": sex})
    pd_path = params_dir or cfg.resolved_params_dir

    try:
        params = _load_params(country.upper(), pd_path)
    except FileNotFoundError as e:
        console.print(f"[red]{e}[/]")
        raise typer.Exit(1)

    try:
        avg_wage = _resolve_average_wage(params, cfg, ref_year)
    except RuntimeError as e:
        console.print(f"[red]{e}[/]")
        raise typer.Exit(1)

    # Resolve wage: if zero, use 1×AW
    if wage == 0.0:
        wage = avg_wage if wage_unit == "currency" else 1.0

    assumptions = load_assumptions(cfg.assumptions_file, pd_path)
    un_client = UNDataPortalClient(cache_ttl_seconds=cfg.cache_ttl_seconds * 4)
    pw_calc = PensionWealthCalculator(assumptions, country.upper(), un_client)
    try:
        survival_factor = pw_calc.annuity_factor(sex=sex)
    except Exception:
        survival_factor = None

    engine = PensionEngine(
        country_params=params,
        assumptions=assumptions,
        average_wage=avg_wage,
        survival_factor=survival_factor,
    )

    person = PersonProfile(
        sex=sex.lower(),
        age=age,
        service_years=service_years,
        wage=wage,
        wage_unit=wage_unit,
        worker_type_id=worker_type,
    )

    result = engine.compute_benefit(person)

    if output == "json":
        import json

        def _asdict(obj):
            if hasattr(obj, "__dataclass_fields__"):
                return {k: _asdict(v) for k, v in dataclasses.asdict(obj).items()}
            if hasattr(obj, "value"):
                return obj.value
            return obj

        console.print(json.dumps(dataclasses.asdict(result), default=str, indent=2))
        return

    # Text output
    ccode = params.metadata.currency_code
    cname = params.metadata.country_name
    console.print(f"\n[bold]{cname} – Pension Calculator[/]")
    console.print(f"Worker type: {result.worker_type_id}")
    console.print()

    elig = result.eligibility
    if elig.is_eligible:
        console.print("[green]Eligibility: ELIGIBLE[/]")
    else:
        console.print("[red]Eligibility: NOT YET ELIGIBLE[/]")
        for m in elig.missing:
            console.print(f"  • {m}")

    console.print(f"  Normal retirement age: {elig.normal_retirement_age:.0f}")
    if elig.early_retirement_age:
        console.print(f"  Early retirement age: {elig.early_retirement_age:.0f}")

    if result.warnings:
        console.print()
        for w in result.warnings:
            console.print(f"[yellow]Warning: {w}[/]")

    console.print()
    console.print(
        f"Gross pension: [bold]{ccode} {result.gross_benefit:,.0f}/yr[/] "
        f"({result.gross_replacement_rate * 100:.1f}% RR)"
    )
    console.print(
        f"Net pension:   [bold]{ccode} {result.net_benefit:,.0f}/yr[/] "
        f"({result.net_replacement_rate * 100:.1f}% RR)"
    )

    if result.component_breakdown:
        console.print()
        console.print("Component breakdown:")
        for sid, val in result.component_breakdown.items():
            if val > 0:
                console.print(f"  → {sid}: {ccode} {val:,.0f}")

    if result.reasoning_trace:
        console.print()
        console.print("[dim]Reasoning:[/]")
        for step in result.reasoning_trace:
            console.print(f"  [dim]{step.label}:[/] {step.value}")

    console.print()


if __name__ == "__main__":
    app()
