"""Bulk enrichment script for country YAML parameter files.

Run once:
    python scripts/bulk_enrich_yaml.py

What it does:
1. Loops all data/params/*.yaml (skips assumptions.yaml, _template.yaml)
2. Skips files that already have coverage_rate (protects hand-curated data)
3. Fetches World Bank ASPIRE coverage indicator (per_si_cp.cov_pop_tot)
4. Adds coverage_rate block if WB returns a non-null value
5. Adds reform_status: stable to any active scheme missing that field
6. Validates the enriched file via Pydantic; restores from backup on failure
7. Prints a summary: Updated N | Skipped N | Errors N
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import yaml

# Ensure project root is importable
_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from pensions_panorama.schema.params_schema import load_country_params
from pensions_panorama.sources.worldbank import WorldBankClient

PARAMS_DIR = _ROOT / "data" / "params"
WB_INDICATOR = "per_si_cp.cov_pop_tot"
WB_START = 2010
WB_END = 2023

_SKIP_FILES = {"assumptions.yaml", "_template.yaml"}


def _most_recent_value(df) -> tuple[float, int] | tuple[None, None]:
    """Return (value, year) for the most recent non-null row, or (None, None)."""
    if df.empty:
        return None, None
    df_sorted = df.dropna(subset=["value"]).sort_values("date", ascending=False)
    if df_sorted.empty:
        return None, None
    row = df_sorted.iloc[0]
    try:
        return float(row["value"]), int(row["date"])
    except (ValueError, TypeError):
        return None, None


def main() -> None:
    wb = WorldBankClient()
    yaml_files = sorted(
        p for p in PARAMS_DIR.glob("*.yaml") if p.name not in _SKIP_FILES
    )

    n_updated = 0
    n_skipped = 0
    n_errors = 0

    for path in yaml_files:
        iso3 = path.stem.upper()

        # Load raw YAML
        raw = path.read_text(encoding="utf-8")
        try:
            data = yaml.safe_load(raw)
        except yaml.YAMLError as exc:
            print(f"[WARN] {iso3}: YAML parse error — {exc}")
            n_errors += 1
            continue

        if data is None:
            n_skipped += 1
            continue

        changed = False

        # ── 1. coverage_rate ──────────────────────────────────────────────
        if "coverage_rate" in data:
            pass  # already present, don't overwrite
        else:
            try:
                df = wb.fetch_indicator(iso3, WB_INDICATOR, WB_START, WB_END)
                val, yr = _most_recent_value(df)
                if val is not None:
                    # Clamp to [0, 1] — indicator is sometimes expressed as 0-100
                    if val > 1.0:
                        val = val / 100.0
                    val = round(min(max(val, 0.0), 1.0), 4)
                    data["coverage_rate"] = {
                        "value": val,
                        "source_citation": (
                            f"World Bank ASPIRE {WB_INDICATOR}, most recent year."
                        ),
                        "year": yr,
                    }
                    changed = True
            except Exception as exc:
                print(f"[WARN] {iso3}: WB fetch failed — {exc}")

        # ── 2. reform_status on active schemes ────────────────────────────
        schemes = data.get("schemes") or []
        for scheme in schemes:
            if not isinstance(scheme, dict):
                continue
            if scheme.get("active", True) and "reform_status" not in scheme:
                scheme["reform_status"] = "stable"
                changed = True

        if not changed:
            n_skipped += 1
            continue

        # ── 3. Write + validate ───────────────────────────────────────────
        backup = path.with_suffix(".yaml.bak")
        shutil.copy2(path, backup)
        try:
            new_content = yaml.dump(data, allow_unicode=True, sort_keys=False)
            path.write_text(new_content, encoding="utf-8")
            load_country_params(path)  # Pydantic validation
            backup.unlink(missing_ok=True)
            n_updated += 1
            print(f"[OK]   {iso3}")
        except Exception as exc:
            # Restore backup
            shutil.copy2(backup, path)
            backup.unlink(missing_ok=True)
            print(f"[ERR]  {iso3}: validation failed — {exc}")
            n_errors += 1

    print(f"\nDone — Updated {n_updated} | Skipped {n_skipped} | Errors {n_errors}")


if __name__ == "__main__":
    main()
