"""ILOSTAT SDMX API client.

Pulls average-earnings data from the ILO SDMX REST endpoint.
Primary series: EAR_4MTH_SEX_ECO_CUR_NB (Mean monthly earnings by sex,
economic activity, and currency – national currency).

The annual average wage is derived by taking the most recent annual
average of the monthly series (sex=SEX_T, economic activity=ECO_TOTAL).

If the series is unavailable for a country, a warning is logged and
the caller should fall back to the manual_value field in the
AverageEarnings schema.

Reference
---------
SDMX REST API:  https://sdmx.ilo.org/rest
Documentation:   https://ilostat.ilo.org/resources/sdmx-tools/
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

from pensions_panorama.config import ILO_CACHE_DIR

logger = logging.getLogger(__name__)

ILO_SDMX_BASE = "https://sdmx.ilo.org/rest"
_DEFAULT_TIMEOUT = 60

# Default series for mean monthly earnings (total, all activities, national currency)
DEFAULT_EARNINGS_INDICATOR = "EAR_4MTH_SEX_ECO_CUR_NB"

# SDMX dimension filter values for "total" sex and "total" economic activity
_SEX_TOTAL = "SEX_T"
_ECO_TOTAL = "ECO_TOTAL"
_CUR_NATIONAL = "CUR_LCU"  # Local currency units


class ILOStatClient:
    """Client for the ILOSTAT SDMX REST API."""

    def __init__(
        self,
        cache_dir: Path = ILO_CACHE_DIR,
        cache_ttl_seconds: int = 7 * 86_400,
    ) -> None:
        cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache = diskcache.Cache(str(cache_dir))
        self._ttl = cache_ttl_seconds
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Accept": "application/vnd.sdmx.data+json;version=1.0",
                "User-Agent": "pensions-panorama/0.1",
            }
        )

    # ------------------------------------------------------------------
    # Retry-wrapped GET
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
    # SDMX parsing helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_sdmx_json(payload: dict[str, Any]) -> pd.DataFrame:
        """Extract a flat DataFrame from an SDMX-JSON 1.0 data message.

        Returns DataFrame with columns corresponding to SDMX dimensions
        plus an ``obs_value`` column.
        """
        try:
            ds = payload["data"]["dataSets"][0]
            struct = payload["data"]["structure"]
        except (KeyError, IndexError, TypeError):
            return pd.DataFrame()

        # Build dimension index from structure metadata
        dimensions = struct.get("dimensions", {}).get("observation", [])
        dim_names = [d["id"] for d in dimensions]
        dim_values: list[list[str]] = [
            [v["id"] for v in d.get("values", [])] for d in dimensions
        ]

        rows: list[dict[str, Any]] = []
        for obs_key, obs_vals in ds.get("observations", {}).items():
            parts = obs_key.split(":")
            row: dict[str, Any] = {}
            for i, part in enumerate(parts):
                if i < len(dim_names) and int(part) < len(dim_values[i]):
                    row[dim_names[i]] = dim_values[i][int(part)]
                else:
                    row[f"dim_{i}"] = part
            row["obs_value"] = obs_vals[0] if obs_vals else None
            rows.append(row)

        return pd.DataFrame(rows)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fetch_earnings_series(
        self,
        iso3: str,
        indicator: str = DEFAULT_EARNINGS_INDICATOR,
        start_year: int = 2015,
        end_year: int = 2023,
        sex: str = _SEX_TOTAL,
        eco: str = _ECO_TOTAL,
    ) -> pd.DataFrame:
        """Fetch an ILOSTAT earnings series for one country.

        Parameters
        ----------
        iso3:
            ISO 3166-1 alpha-3 code (e.g. ``"JOR"``).
        indicator:
            ILOSTAT dataflow identifier.
        start_year / end_year:
            Year range (inclusive).
        sex:
            SDMX sex dimension value (default ``"SEX_T"`` = total).
        eco:
            SDMX economic-activity dimension value (default ``"ECO_TOTAL"``).

        Returns
        -------
        pd.DataFrame with columns: ``ref_area``, ``sex``, ``eco``, ``time_period``,
        ``obs_value`` (monthly earnings in national currency).
        Empty DataFrame if unavailable.
        """
        cache_key = f"ilo_{iso3}_{indicator}_{sex}_{eco}_{start_year}_{end_year}"
        if cache_key in self._cache:
            logger.debug("Cache hit: %s", cache_key)
            return self._cache[cache_key]

        # SDMX REST key format: indicator/ref_area.sex.eco.currency.?
        # We use the generic filter path and let the API return all
        # dimensions, then filter locally.
        url = (
            f"{ILO_SDMX_BASE}/data/{indicator}"
            f"/{iso3}.{sex}.{eco}../"
            f"?startPeriod={start_year}&endPeriod={end_year}&detail=dataonly"
        )
        try:
            payload = self._get_json(url)
        except requests.HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 404:
                logger.warning(
                    "ILOSTAT series %s not found for %s", indicator, iso3
                )
                return pd.DataFrame()
            logger.error("ILOSTAT fetch error for %s/%s: %s", iso3, indicator, exc)
            return pd.DataFrame()
        except requests.RequestException as exc:
            logger.error("ILOSTAT request failed for %s/%s: %s", iso3, indicator, exc)
            return pd.DataFrame()

        df = self._parse_sdmx_json(payload)
        if df.empty:
            logger.warning("Empty ILOSTAT response for %s/%s", iso3, indicator)
            self._cache.set(cache_key, df, expire=self._ttl)
            return df

        df["obs_value"] = pd.to_numeric(df.get("obs_value", pd.Series()), errors="coerce")
        df = df.rename(columns={"TIME_PERIOD": "time_period", "REF_AREA": "ref_area"})

        self._cache.set(cache_key, df, expire=self._ttl)
        logger.info(
            "Fetched %d ILOSTAT observations for %s/%s", len(df), iso3, indicator
        )
        return df

    def get_average_annual_earnings(
        self,
        iso3: str,
        ref_year: int,
        indicator: str = DEFAULT_EARNINGS_INDICATOR,
        transformation: str | None = None,
    ) -> float | None:
        """Return the annual average earnings for a country in national currency.

        Looks for data in the ref_year; falls back to the nearest prior year
        with non-null data.

        Parameters
        ----------
        transformation:
            Optional Python expression using ``x`` as the raw monthly value.
            E.g. ``"x * 12"`` to annualise monthly data.
        """
        df = self.fetch_earnings_series(
            iso3=iso3,
            indicator=indicator,
            start_year=ref_year - 5,
            end_year=ref_year,
        )
        if df.empty or "obs_value" not in df.columns:
            logger.warning(
                "No ILOSTAT earnings data for %s; manual value needed.", iso3
            )
            return None

        # Identify time period column
        time_col = "time_period" if "time_period" in df.columns else "TIME_PERIOD"
        if time_col not in df.columns:
            # Try to find any column that looks like a year
            candidates = [c for c in df.columns if "time" in c.lower() or "period" in c.lower()]
            time_col = candidates[0] if candidates else None

        if time_col:
            df["_year"] = df[time_col].astype(str).str[:4]
            df["_year"] = pd.to_numeric(df["_year"], errors="coerce")
            valid = df.dropna(subset=["obs_value", "_year"])
            target = valid[valid["_year"] == ref_year]
            if target.empty:
                target = valid[valid["_year"] <= ref_year].sort_values("_year")
            if target.empty:
                return None
            raw_value = float(target["obs_value"].mean())
        else:
            valid = df.dropna(subset=["obs_value"])
            if valid.empty:
                return None
            raw_value = float(valid["obs_value"].mean())

        # Apply transformation expression if provided
        if transformation:
            try:
                x = raw_value  # noqa: F841 – used in eval
                raw_value = float(eval(transformation, {"x": x, "__builtins__": {}}))  # noqa: S307
            except Exception as exc:
                logger.error("ILOSTAT transformation '%s' failed: %s", transformation, exc)

        logger.info("ILOSTAT annual earnings for %s ref_year=%d: %.2f", iso3, ref_year, raw_value)
        return raw_value

    def list_available_indicators(self) -> list[str]:
        """Return a list of dataflow IDs available on ILOSTAT SDMX."""
        cache_key = "ilo_dataflows"
        if cache_key in self._cache:
            return self._cache[cache_key]

        url = f"{ILO_SDMX_BASE}/dataflow/ILO/all"
        try:
            resp = self._session.get(
                url,
                timeout=_DEFAULT_TIMEOUT,
                headers={"Accept": "application/xml"},
            )
            resp.raise_for_status()
            # Parse XML for dataflow IDs (minimal parsing)
            import re
            ids = re.findall(r'<(?:\w+:)?Dataflow[^>]+id="([^"]+)"', resp.text)
            self._cache.set(cache_key, ids, expire=self._ttl * 4)
            return ids
        except Exception as exc:
            logger.error("Failed to list ILOSTAT dataflows: %s", exc)
            return []
