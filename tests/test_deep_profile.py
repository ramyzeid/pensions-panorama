"""Tests for deep profile builder."""

from __future__ import annotations

import pandas as pd
import pytest

from pensions_panorama.config import RunConfig
from pensions_panorama.deep_profile import builder
from pensions_panorama.schema.params_schema import load_country_params


class DummyWB:
    def fetch_indicator(self, country: str, indicator: str, start_year: int, end_year: int) -> pd.DataFrame:
        return pd.DataFrame([
            {
                "countryiso3code": country,
                "indicator_id": indicator,
                "date": 2022,
                "value": 123.45,
            }
        ])


def test_scheme_ordering():
    mapping = {
        "schemes": [
            {"scheme_id": "B", "scheme_name": "DB Main", "scheme_type_group": "db"},
            {"scheme_id": "A", "scheme_name": "Social Pension", "scheme_type_group": "noncontrib"},
            {"scheme_id": "C", "scheme_name": "Mandatory DC", "scheme_type_group": "dc"},
        ]
    }
    schemes = builder._build_schemes(mapping)
    assert [s.scheme_type_group.value for s in schemes] == ["noncontrib", "dc", "db"]


def test_costa_rica_structure():
    params = load_country_params(
        builder.DEEP_PROFILE_MAPPING_DIR.parent / "params" / "CRI.yaml"
    )
    cfg = RunConfig(ref_year=2023, start_year=2010, end_year=2023)
    profile = builder.build_deep_profile("CRI", params, cfg, DummyWB(), offline=True)

    keys = [item.key for item in profile.country_indicators]
    assert "year" in keys
    assert len(profile.country_indicators) >= 5
    assert len(profile.system_kpis) == 5
    assert profile.narrative.text
    assert len(profile.schemes) >= 1


def test_not_available_cells():
    cfg = RunConfig(ref_year=2023, start_year=2010, end_year=2023)
    kpis = builder._build_system_kpis({}, "CRI", DummyWB(), cfg, offline=True)
    assert all(k.cell.value is None for k in kpis)


def test_auto_enrichment_from_params():
    """Countries without a mapping file still get scheme data from their params YAML."""
    params = load_country_params(
        builder.DEEP_PROFILE_MAPPING_DIR.parent / "params" / "KEN.yaml"
    )
    cfg = RunConfig(ref_year=2023, start_year=2010, end_year=2023)
    profile = builder.build_deep_profile("KEN", params, cfg, DummyWB(), offline=True)

    assert len(profile.schemes) >= 1
    s = profile.schemes[0]
    attrs = s.attributes

    # Contribution rates should be auto-filled (stored as %)
    assert attrs["contrib_employee"].value is not None
    assert attrs["contrib_employer"].value is not None
    assert attrs["contrib_total"].value is not None
    assert attrs["contrib_total"].value == pytest.approx(
        attrs["contrib_employee"].value + attrs["contrib_employer"].value, rel=1e-3
    )

    # Retirement ages should be auto-filled
    assert attrs["ret_age_male"].value is not None
    assert attrs["ret_age_female"].value is not None

    # Narrative should be non-empty
    assert "Kenya" in profile.narrative.text


def test_auto_narrative_fallback_includes_rates():
    """Auto-generated narrative includes contribution rates."""
    params = load_country_params(
        builder.DEEP_PROFILE_MAPPING_DIR.parent / "params" / "KEN.yaml"
    )
    cfg = RunConfig(ref_year=2023, start_year=2010, end_year=2023)
    profile = builder.build_deep_profile("KEN", params, cfg, DummyWB(), offline=True)
    # Should mention contribution info
    assert "%" in profile.narrative.text or "contribution" in profile.narrative.text.lower()


def test_scheme_type_group_dc():
    """DC params file produces dc scheme_type_group."""
    params = load_country_params(
        builder.DEEP_PROFILE_MAPPING_DIR.parent / "params" / "KEN.yaml"
    )
    schemes = builder._build_schemes({}, params)
    assert all(s.scheme_type_group.value in ("noncontrib", "dc", "db") for s in schemes)
    assert schemes[0].scheme_type_group.value == "dc"
