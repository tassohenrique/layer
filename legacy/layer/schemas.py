"""Schemas Pydantic v2 — validação de entrada e serialização."""
from __future__ import annotations

import datetime as _dt

from pydantic import BaseModel, ConfigDict, Field, field_validator

from layer.domain.families import OlfactoryFamily
from layer.domain.seasons import Season
from layer.models import Concentration, Gender, HouseType, Intention, Occasion


class FragranceBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    brand: str = Field(min_length=1, max_length=120)
    house_type: HouseType
    gender: Gender
    concentration: Concentration
    intensity: int = Field(ge=1, le=5)
    longevity_hours: int = Field(ge=1, le=24)

    primary_family: OlfactoryFamily
    secondary_family: OlfactoryFamily | None = None

    notes_top: list[str] = Field(default_factory=list)
    notes_heart: list[str] = Field(default_factory=list)
    notes_base: list[str] = Field(default_factory=list)

    best_season: list[Season] = Field(default_factory=list)

    owned: bool = True
    bottle_ml: int = Field(default=100, ge=1)
    ml_remaining: int = Field(default=100, ge=0)
    personal_rating: int | None = Field(default=None, ge=1, le=5)
    price_tier: int = Field(default=2, ge=1, le=4)

    notes_pessoais: str = ""

    @field_validator("ml_remaining")
    @classmethod
    def ml_remaining_not_above_bottle(cls, v: int, info) -> int:
        bottle_ml = info.data.get("bottle_ml")
        if bottle_ml is not None and v > bottle_ml:
            raise ValueError("ml_remaining não pode ser maior que bottle_ml")
        return v


class FragranceCreate(FragranceBase):
    pass


class FragranceUpdate(BaseModel):
    """Todos os campos opcionais — usado em updates parciais."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    brand: str | None = None
    house_type: HouseType | None = None
    gender: Gender | None = None
    concentration: Concentration | None = None
    intensity: int | None = Field(default=None, ge=1, le=5)
    longevity_hours: int | None = Field(default=None, ge=1, le=24)
    primary_family: OlfactoryFamily | None = None
    secondary_family: OlfactoryFamily | None = None
    notes_top: list[str] | None = None
    notes_heart: list[str] | None = None
    notes_base: list[str] | None = None
    best_season: list[Season] | None = None
    owned: bool | None = None
    bottle_ml: int | None = Field(default=None, ge=1)
    ml_remaining: int | None = Field(default=None, ge=0)
    personal_rating: int | None = Field(default=None, ge=1, le=5)
    price_tier: int | None = Field(default=None, ge=1, le=4)
    notes_pessoais: str | None = None


class FragranceRead(FragranceBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class ComboRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    base_fragrance_id: int
    modifier_fragrance_id: int
    intention: Intention
    compatibility_score: int
    rationale: str
    application_notes: str
    best_season: list[Season]
    occasion: Occasion
    user_rating: int | None
    created_at: _dt.datetime


class JournalEntryCreate(BaseModel):
    date: _dt.date = Field(default_factory=_dt.date.today)
    combo_id: int | None = None
    fragrance_ids: list[int] = Field(default_factory=list)
    weather: str = ""
    occasion: Occasion
    mood_notes: str = ""
    rating: int | None = Field(default=None, ge=1, le=5)
    would_repeat: bool = True


class JournalEntryRead(JournalEntryCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
