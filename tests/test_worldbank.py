"""Tests for the World Bank API client with mocked HTTP responses."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import responses as resp_lib


class TestWorldBankClientUnit:
    """Unit tests with mocked responses library."""

    @pytest.fixture
    def wb_client(self, tmp_path):
        from pensions_panorama.sources.worldbank import WorldBankClient
        return WorldBankClient(cache_dir=tmp_path / "wb_cache", cache_ttl_seconds=60)

    @resp_lib.activate
    def test_fetch_indicator_returns_dataframe(self, wb_client, mock_wb_response):
        """Client should parse WB API JSON and return a DataFrame with expected columns."""
        resp_lib.add(
            resp_lib.GET,
            "https://api.worldbank.org/v2/country/JOR/indicator/FP.CPI.TOTL.ZG",
            json=mock_wb_response,
            status=200,
        )
        df = wb_client.fetch_indicator("JOR", "FP.CPI.TOTL.ZG", 2021, 2023)
        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert "value" in df.columns
        assert "date" in df.columns

    @resp_lib.activate
    def test_fetch_indicator_caches_result(self, wb_client, mock_wb_response, tmp_path):
        """Second call should be served from cache without a second HTTP request."""
        resp_lib.add(
            resp_lib.GET,
            "https://api.worldbank.org/v2/country/JOR/indicator/FP.CPI.TOTL.ZG",
            json=mock_wb_response,
            status=200,
        )
        df1 = wb_client.fetch_indicator("JOR", "FP.CPI.TOTL.ZG", 2021, 2023)
        df2 = wb_client.fetch_indicator("JOR", "FP.CPI.TOTL.ZG", 2021, 2023)
        # Only one actual HTTP call should have been made
        assert len(resp_lib.calls) == 1
        assert df1.equals(df2)

    @resp_lib.activate
    def test_empty_response_returns_empty_df(self, wb_client):
        """API returning empty data should produce an empty DataFrame."""
        resp_lib.add(
            resp_lib.GET,
            "https://api.worldbank.org/v2/country/ZZZ/indicator/FP.CPI.TOTL.ZG",
            json=[{"page": 1, "pages": 1, "per_page": 1000, "total": 0}, None],
            status=200,
        )
        df = wb_client.fetch_indicator("ZZZ", "FP.CPI.TOTL.ZG", 2020, 2023)
        assert isinstance(df, pd.DataFrame)
        assert df.empty

    @resp_lib.activate
    def test_get_latest_value(self, wb_client, mock_wb_response):
        resp_lib.add(
            resp_lib.GET,
            "https://api.worldbank.org/v2/country/JOR/indicator/FP.CPI.TOTL.ZG",
            json=mock_wb_response,
            status=200,
        )
        val = wb_client.get_latest_value("JOR", "FP.CPI.TOTL.ZG", 2021, 2023)
        # Latest value in mock is 2.1 (2023)
        assert val == pytest.approx(2.1, abs=0.01)

    @resp_lib.activate
    def test_404_returns_empty_df(self, wb_client):
        """HTTP 404 should be caught and return empty DataFrame without crashing."""
        resp_lib.add(
            resp_lib.GET,
            "https://api.worldbank.org/v2/country/ZZZ/indicator/FAKE.IND",
            status=404,
        )
        # Should not raise, should return empty DF
        df = wb_client.fetch_indicator("ZZZ", "FAKE.IND", 2020, 2023)
        assert isinstance(df, pd.DataFrame)


class TestWorldBankCountryMetadata:
    """Test country metadata fetching."""

    @pytest.fixture
    def wb_client(self, tmp_path):
        from pensions_panorama.sources.worldbank import WorldBankClient
        return WorldBankClient(cache_dir=tmp_path / "wb_cache", cache_ttl_seconds=60)

    @resp_lib.activate
    def test_get_country_metadata(self, wb_client):
        mock_meta = [
            {"page": 1, "pages": 1, "per_page": 1000, "total": 1},
            [
                {
                    "id": "JOR",
                    "iso2Code": "JO",
                    "name": "Jordan",
                    "region": {"id": "MEA", "value": "Middle East & North Africa"},
                    "incomeLevel": {"id": "UMC", "value": "Upper middle income"},
                    "capitalCity": "Amman",
                }
            ],
        ]
        resp_lib.add(
            resp_lib.GET,
            "https://api.worldbank.org/v2/country/JOR",
            json=mock_meta,
            status=200,
        )
        df = wb_client.get_country_metadata("JOR")
        assert not df.empty
        assert "name" in df.columns

    @resp_lib.activate
    def test_filter_by_region(self, wb_client):
        mock_all = [
            {"page": 1, "pages": 1, "per_page": 1000, "total": 2},
            [
                {"id": "JOR", "region": {"id": "MEA"}, "name": "Jordan"},
                {"id": "EGY", "region": {"id": "MEA"}, "name": "Egypt"},
                {"id": "FRA", "region": {"id": "ECS"}, "name": "France"},
            ],
        ]
        resp_lib.add(
            resp_lib.GET,
            "https://api.worldbank.org/v2/country/all",
            json=mock_all,
            status=200,
        )
        codes = wb_client.filter_countries_by_region("MEA")
        assert "JOR" in codes
        assert "EGY" in codes
        assert "FRA" not in codes


class TestPensionWealthMath:
    """Unit tests for pension wealth calculations (pure math, no API)."""

    def test_annuity_factor_positive(self, mock_survival_df):
        from pensions_panorama.model.pension_wealth import compute_annuity_factor
        af = compute_annuity_factor(mock_survival_df, discount_rate=0.02)
        assert af > 0

    def test_annuity_factor_decreases_with_higher_discount(self, mock_survival_df):
        from pensions_panorama.model.pension_wealth import compute_annuity_factor
        af_low = compute_annuity_factor(mock_survival_df, discount_rate=0.01)
        af_high = compute_annuity_factor(mock_survival_df, discount_rate=0.05)
        assert af_low > af_high

    def test_annuity_factor_increases_with_indexation(self, mock_survival_df):
        from pensions_panorama.model.pension_wealth import compute_annuity_factor
        af_no_idx = compute_annuity_factor(mock_survival_df, discount_rate=0.03,
                                           indexation_rate=0.0)
        af_with_idx = compute_annuity_factor(mock_survival_df, discount_rate=0.03,
                                              indexation_rate=0.02)
        assert af_with_idx > af_no_idx

    def test_fallback_annuity_factor_formula(self):
        from pensions_panorama.model.pension_wealth import fallback_annuity_factor
        # At d=0, af = life_expectancy
        af = fallback_annuity_factor(20.0, discount_rate=0.0)
        assert abs(af - 20.0) < 1e-6

    def test_fallback_annuity_decreasing_in_discount(self):
        from pensions_panorama.model.pension_wealth import fallback_annuity_factor
        af_2 = fallback_annuity_factor(20.0, discount_rate=0.02)
        af_5 = fallback_annuity_factor(20.0, discount_rate=0.05)
        assert af_2 > af_5

    def test_empty_survival_returns_zero(self):
        import pandas as pd
        from pensions_panorama.model.pension_wealth import compute_annuity_factor
        af = compute_annuity_factor(pd.DataFrame(), discount_rate=0.02)
        assert af == 0.0

    def test_pension_wealth_calculator_uses_fallback(self, default_assumptions):
        from pensions_panorama.model.pension_wealth import PensionWealthCalculator
        # No UN client → must fall back
        calc = PensionWealthCalculator(default_assumptions, iso3="JOR", un_client=None)
        af = calc.annuity_factor(sex="male")
        assert af > 0

    def test_pension_wealth_as_multiple_of_aw(self, default_assumptions):
        from pensions_panorama.model.pension_wealth import PensionWealthCalculator
        calc = PensionWealthCalculator(default_assumptions, iso3="JOR", un_client=None)
        annual_pension = 5000.0
        avg_wage = 10000.0
        pw = calc.compute_pension_wealth(annual_pension, avg_wage, sex="male")
        af = calc.annuity_factor(sex="male")
        expected = (annual_pension / avg_wage) * af
        assert abs(pw - expected) < 1e-9
