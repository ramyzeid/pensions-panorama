"""Configuration loading and path constants.

The run-config YAML drives every run, making outputs fully reproducible when
inputs (API cache + param files) are also pinned.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Canonical directory layout
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
PARAMS_DIR = DATA_DIR / "params"
REPORTS_DIR = BASE_DIR / "reports"
COUNTRY_REPORTS_DIR = REPORTS_DIR / "country"
PANORAMA_DIR = REPORTS_DIR / "panorama_summary"
DEEP_PROFILE_DIR = REPORTS_DIR / "deep_profiles"
TEMPLATES_DIR = Path(__file__).parent / "templates"

# Cache subdirectories
WB_CACHE_DIR = RAW_DIR / "cache" / "worldbank"
UN_CACHE_DIR = RAW_DIR / "cache" / "un_dataportal"
ILO_CACHE_DIR = RAW_DIR / "cache" / "ilostat"


def _ensure_dirs() -> None:
    for d in [
        RAW_DIR,
        PROCESSED_DIR,
        PARAMS_DIR,
        COUNTRY_REPORTS_DIR,
        PANORAMA_DIR,
        DEEP_PROFILE_DIR,
        WB_CACHE_DIR,
        UN_CACHE_DIR,
        ILO_CACHE_DIR,
    ]:
        d.mkdir(parents=True, exist_ok=True)


_ensure_dirs()


# ---------------------------------------------------------------------------
# Run configuration model
# ---------------------------------------------------------------------------
class RunConfig(BaseModel):
    """Top-level run configuration – serializable and deterministic."""

    countries: list[str] = Field(
        default_factory=list,
        description="ISO3 codes of countries to process.",
    )
    ref_year: int = Field(2023, description="Reference year for benefit calculations.")
    start_year: int = Field(2010, description="Earliest year to pull from APIs.")
    end_year: int = Field(2023, description="Latest year to pull from APIs.")
    earnings_multiples: list[float] = Field(
        default=[0.5, 0.75, 1.0, 1.5, 2.0, 2.5],
        description="Earnings multiples (×AW) at which to evaluate pensions.",
    )
    sex: str = Field("male", description="Modeling sex: male | female | total.")
    cache_ttl_days: int = Field(7, description="TTL for API response cache (days).")
    log_level: str = Field("INFO", description="Python logging level.")
    assumptions_file: str = Field(
        "assumptions.yaml",
        description="Filename inside data/params/ for global modeling assumptions.",
    )
    params_dir: str | None = Field(
        None, description="Override path to country params directory."
    )
    reports_dir: str | None = Field(
        None, description="Override path to output reports directory."
    )

    @property
    def cache_ttl_seconds(self) -> int:
        return self.cache_ttl_days * 86_400

    @property
    def resolved_params_dir(self) -> Path:
        return Path(self.params_dir) if self.params_dir else PARAMS_DIR

    @property
    def resolved_reports_dir(self) -> Path:
        return Path(self.reports_dir) if self.reports_dir else REPORTS_DIR


def load_run_config(path: Path | None = None) -> RunConfig:
    """Load RunConfig from a YAML file, falling back to defaults."""
    if path and path.exists():
        with open(path) as fh:
            raw: dict[str, Any] = yaml.safe_load(fh) or {}
        cfg = RunConfig(**raw)
        logger.info("Loaded run config from %s", path)
        return cfg
    logger.info("No run-config file found; using defaults.")
    return RunConfig()


def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
