"""World Bank DataViz / Tableau CSV fetcher.

Pulls data from published Tableau dashboards on dataviz.worldbank.org using
the Tableau Server CSV export endpoint  (no authentication required for public views).

Usage example
-------------
    from pensions_panorama.sources.wb_dataviz import WBDatavizClient

    client = WBDatavizClient()
    df = client.fetch_sheet("PensionsDashboard_17389403751160", "KSSocialInsurance")
    print(df)

See also: ``scripts/fetch_pensions_dashboard.py`` for a full extraction run.
"""

from __future__ import annotations

import io
import logging
import time
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from tenacity import (
    after_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)

DATAVIZ_BASE = "https://dataviz.worldbank.org/views"
_DEFAULT_TIMEOUT = 30  # seconds
_RATE_LIMIT_DELAY = 1.0  # seconds between requests

# ---------------------------------------------------------------------------
# Known sheets for the Pensions Dashboard workbook
# (only sheets that return data via the public CSV endpoint)
# ---------------------------------------------------------------------------
PENSIONS_DASHBOARD_WORKBOOK = "PensionsDashboard_17389403751160"

PENSIONS_DASHBOARD_SHEETS: dict[str, str] = {
    "KSSocialInsurance": "Administrative costs as % of contributions",
    # Add more sheet names here as they become accessible.
    # To probe for new sheets, run:
    #   python scripts/fetch_pensions_dashboard.py --probe
}


class WBDatavizClient:
    """Fetch data from public Tableau views on dataviz.worldbank.org.

    Each Tableau view exposes a ``.csv`` download endpoint:
        GET /views/{workbook}/{sheet}.csv

    The response is a plain CSV with the data currently shown in that view.
    This requires no authentication for publicly published dashboards.
    """

    def __init__(self, cache_dir: Path | None = None, cache_ttl_days: int = 7) -> None:
        self._session = requests.Session()
        self._session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept": "text/csv,application/csv,*/*",
            }
        )
        self._cache_dir = cache_dir
        self._cache_ttl_seconds = cache_ttl_days * 86_400

        if cache_dir is not None:
            cache_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _cache_path(self, workbook: str, sheet: str) -> Path | None:
        if self._cache_dir is None:
            return None
        return self._cache_dir / f"{workbook}__{sheet}.csv"

    def _is_cache_fresh(self, path: Path) -> bool:
        if not path.exists():
            return False
        age = time.time() - path.stat().st_mtime
        return age < self._cache_ttl_seconds

    @retry(
        retry=retry_if_exception_type(requests.RequestException),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=15),
        after=after_log(logger, logging.WARNING),
        reraise=True,
    )
    def _get_csv(self, url: str) -> str:
        resp = self._session.get(url, timeout=_DEFAULT_TIMEOUT)
        resp.raise_for_status()
        return resp.text

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fetch_sheet(
        self,
        workbook: str,
        sheet: str,
        use_cache: bool = True,
    ) -> pd.DataFrame:
        """Download a Tableau sheet as a DataFrame.

        Parameters
        ----------
        workbook:
            Tableau workbook URL name, e.g. ``"PensionsDashboard_17389403751160"``.
        sheet:
            Tableau view (sheet) URL name, e.g. ``"KSSocialInsurance"``.
        use_cache:
            Return cached CSV if fresh (default True).

        Returns
        -------
        pd.DataFrame
            Parsed CSV data.  Empty DataFrame if the sheet is not accessible.
        """
        cache_path = self._cache_path(workbook, sheet)

        # Return cached version if still fresh
        if use_cache and cache_path is not None and self._is_cache_fresh(cache_path):
            logger.debug("Cache hit: %s/%s", workbook, sheet)
            return pd.read_csv(cache_path)

        url = f"{DATAVIZ_BASE}/{workbook}/{sheet}.csv"
        logger.info("Fetching %s", url)

        try:
            raw = self._get_csv(url)
        except requests.HTTPError as exc:
            logger.warning("HTTP %s for %s/%s — skipping", exc.response.status_code, workbook, sheet)
            return pd.DataFrame()
        except requests.RequestException as exc:
            logger.warning("Request failed for %s/%s: %s — skipping", workbook, sheet, exc)
            return pd.DataFrame()

        # Guard: Tableau sometimes returns an HTML error page with HTTP 200
        if not raw.strip() or raw.lstrip().startswith(("{", "<", "!")):
            logger.warning("Non-CSV response for %s/%s — skipping", workbook, sheet)
            return pd.DataFrame()

        df = pd.read_csv(io.StringIO(raw))

        # Cache to disk
        if cache_path is not None:
            cache_path.write_text(raw, encoding="utf-8")
            logger.debug("Cached to %s", cache_path)

        time.sleep(_RATE_LIMIT_DELAY)
        return df

    def fetch_pensions_dashboard(
        self,
        workbook: str = PENSIONS_DASHBOARD_WORKBOOK,
        sheets: list[str] | None = None,
        use_cache: bool = True,
    ) -> dict[str, pd.DataFrame]:
        """Fetch all known sheets from a Pensions Dashboard workbook.

        Parameters
        ----------
        workbook:
            Tableau workbook URL name.
        sheets:
            Explicit list of sheet names to fetch.  Defaults to all entries in
            ``PENSIONS_DASHBOARD_SHEETS``.
        use_cache:
            Pass through to :meth:`fetch_sheet`.

        Returns
        -------
        dict[str, pd.DataFrame]
            Mapping of sheet name → DataFrame (only non-empty results).
        """
        target_sheets = sheets or list(PENSIONS_DASHBOARD_SHEETS.keys())
        results: dict[str, pd.DataFrame] = {}

        for sheet in target_sheets:
            df = self.fetch_sheet(workbook, sheet, use_cache=use_cache)
            if not df.empty:
                results[sheet] = df
                logger.info("  %s: %d rows × %d cols", sheet, len(df), len(df.columns))
            else:
                logger.info("  %s: no data (sheet not accessible)", sheet)

        return results

    def probe_sheets(
        self,
        workbook: str,
        candidates: list[str],
        delay: float = 1.5,
    ) -> list[str]:
        """Probe a list of candidate sheet names and return the accessible ones.

        Useful for discovering new sheets when the workbook is updated.

        Parameters
        ----------
        workbook:
            Tableau workbook URL name.
        candidates:
            Sheet names to test.
        delay:
            Seconds to wait between requests (be polite to the server).

        Returns
        -------
        list[str]
            Sheet names that returned valid CSV data.
        """
        found: list[str] = []
        for sheet in candidates:
            df = self.fetch_sheet(workbook, sheet, use_cache=False)
            if not df.empty:
                logger.info("✓ Found sheet: %s (%d rows)", sheet, len(df))
                found.append(sheet)
            time.sleep(delay)
        return found
