#!/usr/bin/env python3
"""Fetch data from the World Bank DataViz Pensions Dashboard (Tableau).

Dashboard URL:
  https://dataviz.worldbank.org/views/PensionsDashboard_17389403751160/KSSocialInsurance

What this does
--------------
1. Downloads all accessible sheets from the Tableau dashboard to
   ``data/raw/wb_dataviz/``.
2. Writes a combined Parquet file to ``data/processed/wb_dataviz_pensions.parquet``
   with a ``sheet`` column indicating the source.
3. (Optional) --probe mode: tests a wide list of candidate sheet names and
   reports which ones are accessible.

Usage
-----
    # Fetch known sheets (fast)
    python scripts/fetch_pensions_dashboard.py

    # Force re-download (ignore cache)
    python scripts/fetch_pensions_dashboard.py --no-cache

    # Probe for new sheets (slow — ~2 min, rate-limited)
    python scripts/fetch_pensions_dashboard.py --probe

Findings
--------
The Tableau CSV export endpoint works without authentication for public views:
    GET https://dataviz.worldbank.org/views/{workbook}/{sheet}.csv

As of 2026-03, the following sheets are publicly accessible:

  KSSocialInsurance  — Administrative costs as % of employer + employee contributions
                        Columns: Program name | Year | Admin cost %
                        Source program: "Statutory Pension Scheme"
                        Year range: 2015–2022

Other sheets in the dashboard either require a logged-in Tableau session or
are not yet part of the public embed.  Run --probe after any dashboard update
to discover newly accessible sheets.

Integration notes
-----------------
The admin-cost metric (PENSIONS_DASHBOARD_SHEETS["KSSocialInsurance"]) can be
added to country YAML params or the pensions_panorama deep-profile JSONs under
a new ``administrative_costs`` key.  See the example at the bottom of this
script.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Allow running directly without installing the package
ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd

from pensions_panorama.config import PROCESSED_DIR, RAW_DIR
from pensions_panorama.sources.wb_dataviz import (
    PENSIONS_DASHBOARD_SHEETS,
    PENSIONS_DASHBOARD_WORKBOOK,
    WBDatavizClient,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Candidate sheet names to probe (run with --probe)
# Extend this list whenever the dashboard is updated.
# ---------------------------------------------------------------------------
PROBE_CANDIDATES = [
    # Key Statistics variants
    "KSSocialInsurance", "KSActiveMembers", "KSPensioners", "KSContributions",
    "KSRevenues", "KSExpenditures", "KSBenefits", "KSAssets", "KSBalance",
    "KSReplacementRate", "KSCoverage", "KSRatio", "KSInvestment", "KSReserves",
    "KSGender", "KSDisability", "KSSurvivors", "KSOldAge",
    # Generic names
    "Overview", "Summary", "KeyStats", "Coverage", "Adequacy", "Expenditure",
    "Revenues", "Benefits", "Contributions", "Demographics", "Sustainability",
    "Reform", "Dashboard", "Finances", "Performance", "Indicators",
    "FinancialSustainability", "CoverageParticipation", "BenefitsAdequacy",
    "ReplacementRate", "GrossReplacement", "NetReplacement", "PensionWealth",
    "OldAgePoverty", "PublicSpending", "GDPShare", "SystemDesign",
    "ActiveMembers", "Pensioners", "Contributors", "PensionPayments",
    "SystemRatio", "AverageBenefit", "AverageWage", "InvestmentReturns",
    "TotalAssets", "FundBalance", "AdminCosts", "GenderGap",
]

CACHE_DIR = RAW_DIR / "cache" / "wb_dataviz"
OUTPUT_PARQUET = PROCESSED_DIR / "wb_dataviz_pensions.parquet"
OUTPUT_CSV = PROCESSED_DIR / "wb_dataviz_pensions.csv"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--no-cache", action="store_true", help="Ignore cached data and re-fetch")
    parser.add_argument("--probe", action="store_true", help="Probe candidate sheet names (~2 min)")
    parser.add_argument(
        "--workbook",
        default=PENSIONS_DASHBOARD_WORKBOOK,
        help=f"Tableau workbook URL name (default: {PENSIONS_DASHBOARD_WORKBOOK})",
    )
    args = parser.parse_args()

    client = WBDatavizClient(cache_dir=CACHE_DIR)

    # ------------------------------------------------------------------
    # Probe mode: discover accessible sheets
    # ------------------------------------------------------------------
    if args.probe:
        logger.info("Probing %d candidate sheet names (this takes ~2 min)...", len(PROBE_CANDIDATES))
        found = client.probe_sheets(args.workbook, PROBE_CANDIDATES, delay=1.5)
        print("\n" + "=" * 60)
        print(f"Accessible sheets ({len(found)} found):")
        for name in found:
            print(f"  ✓  {name}")
        print("=" * 60)
        print("\nAdd newly found sheets to PENSIONS_DASHBOARD_SHEETS in")
        print("  pensions_panorama/sources/wb_dataviz.py")
        return

    # ------------------------------------------------------------------
    # Normal mode: fetch all known sheets
    # ------------------------------------------------------------------
    logger.info("Workbook: %s", args.workbook)
    logger.info("Known sheets: %s", list(PENSIONS_DASHBOARD_SHEETS.keys()))

    all_data = client.fetch_pensions_dashboard(
        workbook=args.workbook,
        use_cache=not args.no_cache,
    )

    if not all_data:
        logger.error("No data retrieved. Check connectivity or run with --probe.")
        sys.exit(1)

    # Combine sheets into one DataFrame with a 'sheet' label column
    frames = []
    for sheet_name, df in all_data.items():
        df = df.copy()
        df.insert(0, "sheet", sheet_name)
        df.insert(1, "description", PENSIONS_DASHBOARD_SHEETS.get(sheet_name, ""))
        frames.append(df)

    combined = pd.concat(frames, ignore_index=True)

    # Save outputs
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    combined.to_parquet(OUTPUT_PARQUET, index=False)
    combined.to_csv(OUTPUT_CSV, index=False)

    logger.info("")
    logger.info("Saved:")
    logger.info("  %s  (%d rows)", OUTPUT_PARQUET, len(combined))
    logger.info("  %s", OUTPUT_CSV)

    # ------------------------------------------------------------------
    # Print a summary
    # ------------------------------------------------------------------
    print("\n" + "=" * 60)
    print(f"WB DataViz Pensions Dashboard  —  {args.workbook}")
    print("=" * 60)
    for sheet_name, df in all_data.items():
        print(f"\n  [{sheet_name}]  {PENSIONS_DASHBOARD_SHEETS.get(sheet_name, '')}")
        print(df.to_string(index=False))
    print("\n" + "=" * 60)
    print(f"Total rows: {len(combined)}")
    print(f"Parquet:    {OUTPUT_PARQUET}")
    print(f"CSV:        {OUTPUT_CSV}")

    # ------------------------------------------------------------------
    # Example: show how to use the admin-cost data
    # ------------------------------------------------------------------
    if "KSSocialInsurance" in all_data:
        df_admin = all_data["KSSocialInsurance"]
        cost_col = [c for c in df_admin.columns if "cost" in c.lower() or "admin" in c.lower()]
        if cost_col:
            latest = df_admin.sort_values("Year").iloc[-1]
            print(
                f"\n  Latest admin cost ({int(latest['Year'])}): "
                f"{latest[cost_col[0]]:.2f}% of contributions"
            )
            print(
                "  → Add to country YAML as:\n"
                "       administrative_cost_pct_contributions:\n"
                f"         value: {latest[cost_col[0]]:.4f}\n"
                f"         year: {int(latest['Year'])}\n"
                "         source: 'WB DataViz Pensions Dashboard (KSSocialInsurance)'"
            )


if __name__ == "__main__":
    main()
