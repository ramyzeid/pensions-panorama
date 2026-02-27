"""Deep profile schema for country-level pension profiles."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SchemeTypeGroup(str, Enum):
    noncontrib = "noncontrib"
    dc = "dc"
    db = "db"


class SourceRef(BaseModel):
    source_name: str | None = None
    source_url: str | None = None
    indicator_id: str | None = None
    year: int | None = None
    notes: str | None = None


class CellValue(BaseModel):
    value: float | int | str | None = None
    unit: str | None = None
    year: int | None = None
    source: SourceRef | None = None
    notes: str | None = None


class NarrativeBlock(BaseModel):
    text: str
    sources: list[SourceRef] = Field(default_factory=list)


class IndicatorItem(BaseModel):
    key: str
    label: str
    cell: CellValue


class SchemeItem(BaseModel):
    scheme_id: str
    scheme_name: str
    scheme_type_group: SchemeTypeGroup
    attributes: dict[str, CellValue]


class SsaUpdateItem(BaseModel):
    title: str
    url: str
    date: str  # "YYYY-MM"
    topic: str | None = None  # brief description of what the update covers


class DeepProfile(BaseModel):
    iso3: str
    country_name: str
    last_updated: datetime
    narrative: NarrativeBlock
    country_indicators: list[IndicatorItem]
    system_kpis: list[IndicatorItem]
    schemes: list[SchemeItem]
    ssa_updates: list[SsaUpdateItem] = Field(default_factory=list)

    def model_dump_jsonable(self) -> dict[str, Any]:
        return self.model_dump(mode="json")
