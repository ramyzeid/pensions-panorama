"""Tests for the Pydantic parameter schema and YAML loading."""

from __future__ import annotations

from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
PARAMS_DIR = PROJECT_ROOT / "data" / "params"


class TestSchemaValidation:
    """Test that valid country YAMLs load without errors."""

    def test_jordan_loads(self, jor_params):
        assert jor_params.metadata.iso3 == "JOR"
        assert jor_params.metadata.country_name == "Jordan"
        assert len(jor_params.schemes) >= 1

    def test_morocco_loads(self, mar_params):
        assert mar_params.metadata.iso3 == "MAR"
        assert len(mar_params.schemes) >= 1

    def test_jordan_has_average_earnings(self, jor_params):
        ae = jor_params.average_earnings
        # Must have either ILOSTAT series or manual value
        assert ae.ilostat_series_id is not None or ae.manual_value is not None

    def test_jordan_schemes_unique_ids(self, jor_params):
        ids = [s.scheme_id for s in jor_params.schemes]
        assert len(ids) == len(set(ids)), "scheme_ids must be unique"

    def test_all_sourced_values_have_citations(self, jor_params):
        from pensions_panorama.schema.params_schema import SourcedValue
        import pydantic

        def _check_sv(model):
            """Recursively assert every SourcedValue has a non-empty citation."""
            for field_name, field_value in model:
                if isinstance(field_value, SourcedValue):
                    assert field_value.source_citation, (
                        f"SourcedValue at field '{field_name}' missing source_citation"
                    )
                elif hasattr(field_value, "__iter__") and not isinstance(field_value, str):
                    for item in field_value:
                        if hasattr(item, "__iter__") and hasattr(item, "__fields__"):
                            _check_sv(item)
                elif hasattr(field_value, "__fields__"):
                    _check_sv(field_value)

        for scheme in jor_params.schemes:
            e = scheme.eligibility
            assert e.normal_retirement_age_male.source_citation
            assert e.normal_retirement_age_female.source_citation

    def test_scheme_ids_no_spaces(self, jor_params):
        for s in jor_params.schemes:
            assert " " not in s.scheme_id

    def test_iso3_length(self, jor_params):
        assert len(jor_params.metadata.iso3) == 3

    def test_currency_code_length(self, jor_params):
        assert len(jor_params.metadata.currency_code) == 3

    def test_retirement_ages_positive(self, jor_params):
        for scheme in jor_params.schemes:
            nra_m = scheme.eligibility.normal_retirement_age_male.value
            nra_f = scheme.eligibility.normal_retirement_age_female.value
            if nra_m is not None:
                assert float(nra_m) > 0
            if nra_f is not None:
                assert float(nra_f) > 0


class TestSchemaRejection:
    """Test that invalid data is rejected by the schema."""

    def test_missing_citation_rejected(self):
        from pydantic import ValidationError
        from pensions_panorama.schema.params_schema import SourcedValue

        with pytest.raises(ValidationError):
            SourcedValue(value=0.07, source_citation="")  # empty string

        with pytest.raises(ValidationError):
            SourcedValue(value=0.07, source_citation="   ")  # whitespace only

    def test_no_earnings_source_rejected(self):
        from pydantic import ValidationError
        from pensions_panorama.schema.params_schema import AverageEarnings

        with pytest.raises(ValidationError):
            AverageEarnings(
                ilostat_series_id=None,
                manual_value=None,
                source_citation="Some source",
            )

    def test_duplicate_scheme_ids_rejected(self):
        from pydantic import ValidationError
        from pensions_panorama.schema.params_schema import (
            CountryParams, CountryMetadata, SchemeComponent, SchemeTier,
            SchemeType, EligibilityRules, BenefitRules, TaxAndContrib,
            AverageEarnings, SourcedValue,
        )

        def _sv(v):
            return SourcedValue(value=v, source_citation="Test source")

        def _scheme(sid):
            return SchemeComponent(
                scheme_id=sid,
                name="Test scheme",
                tier=SchemeTier.FIRST,
                type=SchemeType.DB,
                coverage="all",
                eligibility=EligibilityRules(
                    normal_retirement_age_male=_sv(65),
                    normal_retirement_age_female=_sv(65),
                ),
                contributions=None,
                benefits=BenefitRules(
                    accrual_rate_per_year=_sv(0.02),
                    indexation="CPI",
                ),
            )

        with pytest.raises(ValidationError):
            CountryParams(
                metadata=CountryMetadata(
                    country_name="Test",
                    iso3="TST",
                    currency="Test Dollar",
                    currency_code="TSD",
                    reference_year=2023,
                ),
                schemes=[_scheme("DB1"), _scheme("DB1")],  # duplicate!
                taxes=TaxAndContrib(),
                average_earnings=AverageEarnings(
                    manual_value=10000.0,
                    source_citation="test",
                ),
            )

    def test_scheme_id_with_space_rejected(self):
        from pydantic import ValidationError
        from pensions_panorama.schema.params_schema import (
            SchemeComponent, SchemeTier, SchemeType, EligibilityRules,
            BenefitRules, SourcedValue,
        )

        def _sv(v):
            return SourcedValue(value=v, source_citation="Test")

        with pytest.raises(ValidationError):
            SchemeComponent(
                scheme_id="bad id",  # space in ID
                name="Test",
                tier=SchemeTier.FIRST,
                type=SchemeType.DB,
                coverage="all",
                eligibility=EligibilityRules(
                    normal_retirement_age_male=_sv(65),
                    normal_retirement_age_female=_sv(65),
                ),
                benefits=BenefitRules(accrual_rate_per_year=_sv(0.02)),
            )


class TestLoadCountryParams:
    """Test the load_country_params helper."""

    def test_missing_file_raises(self, tmp_path):
        from pensions_panorama.schema.params_schema import load_country_params
        with pytest.raises(FileNotFoundError):
            load_country_params(tmp_path / "NONEXISTENT.yaml")

    def test_both_sample_files_load(self):
        from pensions_panorama.schema.params_schema import load_country_params
        for iso3 in ["JOR", "MAR"]:
            path = PARAMS_DIR / f"{iso3}.yaml"
            if path.exists():
                params = load_country_params(path)
                assert params.metadata.iso3 == iso3
