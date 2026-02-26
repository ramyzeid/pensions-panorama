"""UN Population Division Data Portal API client.

Pulls mortality / life-table data from the World Population Prospects (WPP)
UNDESA API (v1).  The life table is the primary input for computing
survival-weighted pension wealth (present value of benefit stream).

Key function
-----------
get_life_table(iso3, year, sex) → pd.DataFrame
    Columns: age, lx, dx, Lx, Tx, ex
    where lx is the survivor function (radix 100 000).

get_location_id(iso3) → int | None
    Resolves an ISO 3166-1 alpha-3 code to the UN location ID.
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

from pensions_panorama.config import UN_CACHE_DIR

logger = logging.getLogger(__name__)

UN_API_BASE = "https://population.un.org/dataportalapi/api/v1"
_DEFAULT_TIMEOUT = 60

# UN WPP sex codes
_SEX_CODE: dict[str, int] = {"male": 1, "female": 2, "total": 3, "both": 3}

# UN WPP indicator IDs relevant for pension wealth
_IND_LX = 58   # lx – survivors at exact age x  (life-table function)
_IND_EX = 61   # ex – expectation of life at exact age x

# UN WPP variant ID 4 = "Medium"
_VARIANT_MEDIUM = 4


class UNDataPortalClient:
    """Client for the UN DESA World Population Prospects Data Portal API."""

    def __init__(
        self,
        cache_dir: Path = UN_CACHE_DIR,
        cache_ttl_seconds: int = 30 * 86_400,  # 30 days – WPP revisions are rare
    ) -> None:
        cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache = diskcache.Cache(str(cache_dir))
        self._ttl = cache_ttl_seconds
        self._session = requests.Session()
        self._session.headers.update(
            {"Accept": "application/json", "User-Agent": "pensions-panorama/0.1"}
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
    # Location resolution
    # ------------------------------------------------------------------

    def get_location_id(self, iso3: str) -> int | None:
        """Resolve an ISO3 country code to a UN location ID.

        Uses the /locations endpoint with pagination.
        """
        cache_key = f"un_loc_{iso3.upper()}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        page = 1
        while True:
            url = f"{UN_API_BASE}/locations"
            params = {"pageSize": 500, "pageNumber": page, "format": "json"}
            try:
                data = self._get_json(url, params=params)
            except requests.RequestException as exc:
                logger.error("Failed to fetch UN locations (page %d): %s", page, exc)
                return None

            # Response shape: {"data": [...], "paging": {"pageNumber", "pageSize", "pageCount"}}
            records: list[dict[str, Any]] = []
            if isinstance(data, dict):
                records = data.get("data", [])
                paging = data.get("paging", {})
            elif isinstance(data, list):
                records = data
                paging = {}
            else:
                break

            for rec in records:
                if str(rec.get("iso3", "")).upper() == iso3.upper():
                    loc_id: int = int(rec["id"])
                    self._cache.set(cache_key, loc_id, expire=self._ttl * 12)
                    return loc_id

            total_pages = paging.get("pageCount", 1)
            if page >= total_pages:
                break
            page += 1

        logger.warning("UN location ID not found for ISO3=%s", iso3)
        return None

    # ------------------------------------------------------------------
    # Life table
    # ------------------------------------------------------------------

    def _fetch_indicator_data(
        self,
        indicator_id: int,
        location_id: int,
        start_year: int,
        end_year: int,
        sex_code: int,
    ) -> list[dict[str, Any]]:
        """Paginated fetch of a single UN WPP indicator for one location."""
        records: list[dict[str, Any]] = []
        page = 1
        while True:
            url = f"{UN_API_BASE}/data/indicators/{indicator_id}/locations/{location_id}/start/{start_year}/end/{end_year}"
            params = {
                "sex": sex_code,
                "variants": _VARIANT_MEDIUM,
                "format": "json",
                "pageSize": 1000,
                "pageNumber": page,
            }
            try:
                data = self._get_json(url, params=params)
            except requests.RequestException as exc:
                logger.error(
                    "UN API error indicator=%d location=%d: %s", indicator_id, location_id, exc
                )
                break

            if isinstance(data, dict):
                page_recs = data.get("data", [])
                paging = data.get("paging", {})
            elif isinstance(data, list):
                page_recs = data
                paging = {}
            else:
                break

            records.extend(page_recs)

            total_pages = paging.get("pageCount", 1)
            if page >= total_pages:
                break
            page += 1

        return records

    def get_life_table(
        self,
        iso3: str,
        year: int,
        sex: str = "total",
    ) -> pd.DataFrame:
        """Return a life table (lx and ex columns) for pension-wealth calculations.

        Parameters
        ----------
        iso3:
            ISO 3166-1 alpha-3 country code.
        year:
            WPP quinquennial period start year (e.g. 2020 for 2020-2025).
        sex:
            ``"male"``, ``"female"``, or ``"total"`` / ``"both"``.

        Returns
        -------
        pd.DataFrame with columns: ``age``, ``lx``, ``ex``.
        ``lx`` is the survivor function (radix 100 000).
        ``ex`` is remaining life expectancy at exact age.
        Empty DataFrame if data unavailable.
        """
        sex_norm = sex.lower()
        sex_code = _SEX_CODE.get(sex_norm, 3)
        cache_key = f"un_lt_{iso3}_{year}_{sex_norm}"

        if cache_key in self._cache:
            logger.debug("Cache hit: %s", cache_key)
            return self._cache[cache_key]

        loc_id = self.get_location_id(iso3)
        if loc_id is None:
            return pd.DataFrame(columns=["age", "lx", "ex"])

        # Fetch lx (survivors) and ex (life expectancy)
        lx_recs = self._fetch_indicator_data(_IND_LX, loc_id, year, year, sex_code)
        ex_recs = self._fetch_indicator_data(_IND_EX, loc_id, year, year, sex_code)

        def _to_df(recs: list[dict[str, Any]], value_col: str) -> pd.DataFrame:
            if not recs:
                return pd.DataFrame()
            df = pd.json_normalize(recs)
            # Typical columns: ageId, ageName, sex, variant, value, timeLabel, ...
            age_col = "ageId" if "ageId" in df.columns else "age"
            val_col = "value" if "value" in df.columns else None
            if val_col is None or age_col not in df.columns:
                return pd.DataFrame()
            out = df[[age_col, val_col]].rename(columns={age_col: "age", val_col: value_col})
            out["age"] = pd.to_numeric(out["age"], errors="coerce")
            out[value_col] = pd.to_numeric(out[value_col], errors="coerce")
            return out.dropna(subset=["age"]).sort_values("age").reset_index(drop=True)

        df_lx = _to_df(lx_recs, "lx")
        df_ex = _to_df(ex_recs, "ex")

        if df_lx.empty and df_ex.empty:
            logger.warning("No UN life-table data for %s year=%d sex=%s", iso3, year, sex)
            return pd.DataFrame(columns=["age", "lx", "ex"])

        if not df_lx.empty and not df_ex.empty:
            df = df_lx.merge(df_ex, on="age", how="outer").sort_values("age").reset_index(drop=True)
        elif not df_lx.empty:
            df = df_lx
        else:
            df = df_ex

        self._cache.set(cache_key, df, expire=self._ttl)
        logger.info(
            "Fetched UN life table for %s year=%d sex=%s (%d rows)",
            iso3, year, sex, len(df),
        )
        return df

    def get_life_expectancy_at_age(
        self,
        iso3: str,
        age: int,
        year: int,
        sex: str = "total",
    ) -> float | None:
        """Return remaining life expectancy (ex) at a given age.

        Used as a fallback annuity divisor when full survival-weighted PV
        is not needed.
        """
        lt = self.get_life_table(iso3, year, sex)
        if lt.empty or "ex" not in lt.columns:
            return None
        row = lt[lt["age"] == age]
        if row.empty:
            # Try nearest available age
            available = lt["age"].dropna().values
            if len(available) == 0:
                return None
            nearest = available[abs(available - age).argmin()]
            row = lt[lt["age"] == nearest]
        if row.empty:
            return None
        return float(row["ex"].iloc[0])

    def get_survival_probabilities(
        self,
        iso3: str,
        retirement_age: int,
        max_age: int,
        year: int,
        sex: str = "total",
    ) -> pd.DataFrame:
        """Return conditional survival probabilities S(t) = lx(r+t) / lx(r).

        Parameters
        ----------
        retirement_age:
            Age at retirement (age r in the life table).
        max_age:
            Oldest age to include.
        year:
            WPP reference year.

        Returns
        -------
        pd.DataFrame with columns: ``t``, ``age``, ``lx``, ``survival_prob``.
        """
        lt = self.get_life_table(iso3, year, sex)
        if lt.empty or "lx" not in lt.columns:
            return pd.DataFrame()

        lx_at_r_rows = lt[lt["age"] == retirement_age]["lx"]
        if lx_at_r_rows.empty:
            logger.warning("lx at retirement age %d not found in life table.", retirement_age)
            return pd.DataFrame()

        lx_r = float(lx_at_r_rows.iloc[0])
        if lx_r == 0:
            return pd.DataFrame()

        subset = lt[(lt["age"] >= retirement_age) & (lt["age"] <= max_age)].copy()
        subset["t"] = (subset["age"] - retirement_age).astype(int)
        subset["survival_prob"] = subset["lx"] / lx_r
        return subset[["t", "age", "lx", "survival_prob"]].reset_index(drop=True)
