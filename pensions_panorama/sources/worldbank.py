"""World Bank Indicators API client.

Provides:
  - fetch_indicator(country, indicator, start_year, end_year) → pd.DataFrame
  - get_country_metadata(iso3?) → pd.DataFrame
  - filter_countries_by_region(region_code) → list[str]

All responses are cached on disk (diskcache) so repeated runs are
deterministic and API-friendly.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import diskcache
import pandas as pd
import requests
from tenacity import (
    after_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from pensions_panorama.config import WB_CACHE_DIR

logger = logging.getLogger(__name__)

WB_BASE_URL = "https://api.worldbank.org/v2"
_DEFAULT_TIMEOUT = 30  # seconds


class WorldBankClient:
    """Client for the World Bank Indicators REST API (v2)."""

    def __init__(
        self,
        cache_dir: Path = WB_CACHE_DIR,
        cache_ttl_seconds: int = 7 * 86_400,
    ) -> None:
        cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache = diskcache.Cache(str(cache_dir))
        self._ttl = cache_ttl_seconds
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": "pensions-panorama/0.1"})

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @retry(
        retry=retry_if_exception_type(requests.RequestException),
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        after=after_log(logger, logging.WARNING),
        reraise=True,
    )
    def _get_json(self, url: str, params: dict[str, Any] | None = None) -> Any:
        resp = self._session.get(url, params=params, timeout=_DEFAULT_TIMEOUT)
        resp.raise_for_status()
        return resp.json()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fetch_indicator(
        self,
        country: str,
        indicator: str,
        start_year: int,
        end_year: int,
    ) -> pd.DataFrame:
        """Fetch a World Bank indicator time-series for one country.

        Parameters
        ----------
        country:
            ISO2, ISO3, or World Bank country code (e.g. ``"JOR"``).
        indicator:
            World Bank series code (e.g. ``"FP.CPI.TOTL.ZG"``).
        start_year / end_year:
            Inclusive year range.

        Returns
        -------
        pd.DataFrame with columns: countryiso3code, indicator_id, date, value.
        Empty DataFrame if no data found.
        """
        cache_key = f"wb_ind_{country}_{indicator}_{start_year}_{end_year}"
        if cache_key in self._cache:
            logger.debug("Cache hit: %s", cache_key)
            return self._cache[cache_key]

        url = f"{WB_BASE_URL}/country/{country}/indicator/{indicator}"
        records: list[dict[str, Any]] = []
        page = 1

        while True:
            params = {
                "format": "json",
                "per_page": 1000,
                "page": page,
                "date": f"{start_year}:{end_year}",
            }
            try:
                payload = self._get_json(url, params=params)
            except requests.RequestException as exc:
                logger.error(
                    "WB fetch failed for %s/%s (page %d): %s", country, indicator, page, exc
                )
                break

            if not payload or len(payload) < 2 or not payload[1]:
                break

            meta: dict[str, Any] = payload[0]
            page_records: list[dict[str, Any]] = payload[1]
            records.extend(page_records)

            if page >= meta.get("pages", 1):
                break
            page += 1

        if not records:
            logger.warning(
                "No World Bank data for country=%s indicator=%s %d-%d",
                country,
                indicator,
                start_year,
                end_year,
            )
            return pd.DataFrame(
                columns=["countryiso3code", "indicator_id", "date", "value"]
            )

        df = pd.json_normalize(records)

        # Standardise columns that appear in the API response
        col_renames: dict[str, str] = {
            "countryiso3code": "countryiso3code",
            "date": "date",
            "value": "value",
        }
        # The indicator column may be nested as indicator.id / indicator.value
        if "indicator.id" in df.columns:
            df = df.rename(columns={"indicator.id": "indicator_id"})
        elif "indicator" in df.columns:
            df["indicator_id"] = indicator

        df = df.rename(columns=col_renames)
        keep = [c for c in ["countryiso3code", "indicator_id", "date", "value"] if c in df.columns]
        df = df[keep].copy()

        df["date"] = pd.to_numeric(df["date"], errors="coerce").astype("Int64")
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df = df.sort_values("date").reset_index(drop=True)

        self._cache.set(cache_key, df, expire=self._ttl)
        logger.info(
            "Fetched %d rows for %s/%s %d-%d", len(df), country, indicator, start_year, end_year
        )
        return df

    def get_latest_value(
        self,
        country: str,
        indicator: str,
        start_year: int,
        end_year: int,
    ) -> float | None:
        """Return the most-recent non-null value for an indicator."""
        df = self.fetch_indicator(country, indicator, start_year, end_year)
        if df.empty or "value" not in df.columns:
            return None
        valid = df.dropna(subset=["value"])
        if valid.empty:
            return None
        return float(valid.iloc[-1]["value"])

    def get_country_metadata(self, iso3: str | None = None) -> pd.DataFrame:
        """Fetch World Bank country metadata (region, income level, etc.).

        Parameters
        ----------
        iso3:
            If supplied, fetch metadata for that country only; otherwise fetch all.
        """
        iso_param = iso3 or "all"
        cache_key = f"wb_meta_{iso_param}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        url = f"{WB_BASE_URL}/country/{iso_param}"
        params = {"format": "json", "per_page": 1000}
        try:
            payload = self._get_json(url, params=params)
        except requests.RequestException as exc:
            logger.error("Failed to fetch WB country metadata: %s", exc)
            return pd.DataFrame()

        if not payload or len(payload) < 2 or not payload[1]:
            return pd.DataFrame()

        df = pd.json_normalize(payload[1])
        self._cache.set(cache_key, df, expire=self._ttl * 4)
        return df

    def filter_countries_by_region(self, region_code: str) -> list[str]:
        """Return ISO3 codes for all countries in a World Bank region.

        Parameters
        ----------
        region_code:
            World Bank region ID, e.g. ``"MEA"`` for Middle East & North Africa.
        """
        meta = self.get_country_metadata()
        if meta.empty:
            return []
        region_col = "region.id" if "region.id" in meta.columns else None
        if region_col is None:
            logger.warning("Could not find region column in WB metadata.")
            return []
        filtered = meta[meta[region_col] == region_code]
        id_col = "id" if "id" in filtered.columns else None
        if id_col is None:
            return []
        return filtered[id_col].dropna().tolist()

    def filter_countries_by_income(self, income_level_code: str) -> list[str]:
        """Return ISO3 codes for all countries at a given World Bank income level."""
        meta = self.get_country_metadata()
        if meta.empty:
            return []
        col = "incomeLevel.id" if "incomeLevel.id" in meta.columns else None
        if col is None:
            return []
        filtered = meta[meta[col] == income_level_code]
        return filtered.get("id", pd.Series()).dropna().tolist()

    # Commonly used macro series
    COMMON_INDICATORS: dict[str, str] = {
        "cpi_inflation_pct": "FP.CPI.TOTL.ZG",
        "gdp_deflator_pct": "NY.GDP.DEFL.KD.ZG",
        "gdp_pc_usd": "NY.GDP.PCAP.CD",
        "gdp_usd": "NY.GDP.MKTP.CD",
        "population_total": "SP.POP.TOTL",
        "population_65plus_pct": "SP.POP.65UP.TO.ZS",
        "life_expectancy_at_birth": "SP.DYN.LE00.IN",
        "old_age_dependency_ratio": "SP.POP.DPND.OL",
    }

    def fetch_macro_context(
        self,
        country: str,
        start_year: int,
        end_year: int,
        indicators: list[str] | None = None,
    ) -> pd.DataFrame:
        """Fetch a set of macro-context indicators and return as a wide DataFrame."""
        to_fetch = indicators or list(self.COMMON_INDICATORS.values())
        frames: list[pd.DataFrame] = []
        for ind in to_fetch:
            df = self.fetch_indicator(country, ind, start_year, end_year)
            if not df.empty and "value" in df.columns:
                df = df[["date", "value"]].rename(columns={"value": ind})
                frames.append(df.set_index("date"))
        if not frames:
            return pd.DataFrame()
        wide = frames[0]
        for f in frames[1:]:
            wide = wide.join(f, how="outer")
        return wide.reset_index()
