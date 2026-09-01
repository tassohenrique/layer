"""Modelos SQLAlchemy 2.x (ORM) para o banco local ``layer.db``."""
from __future__ import annotations

import datetime as _dt
from enum import Enum

from sqlalchemy import JSON, Enum as SAEnum, ForeignKey, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator

from layer.domain.families import OlfactoryFamily
from layer.domain.seasons import Season


class Base(DeclarativeBase):
    pass


class SeasonListType(TypeDecorator):
    """Lista de `Season` persistida como JSON de strings.

    O tipo `JSON` puro do SQLAlchemy não sabe reconstruir enums ao ler do
    banco (devolve `list[str]` cru) — este decorator faz essa conversão nos
    dois sentidos para que o restante do código sempre veja `list[Season]`.
    """

    impl = JSON
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return [v.value if isinstance(v, Season) else v for v in value]

    def process_result_value(self, value, dialect):
        if value is None:
            return []
        return [Season(v) for v in value]


class HouseType(str, Enum):
    NICHO = "nicho"
    DESIGNER = "designer"


class Gender(str, Enum):
    UNISSEX = "unissex"
    MASC = "masc"
    FEM = "fem"


class Concentration(str, Enum):
    COLOGNE = "cologne"
    EDT = "edt"
    EDP = "edp"
    EXTRAIT = "extrait"


# Ordem de "força" das concentrações, usada pelo motor de compatibilidade
# para desempate de papel líder/modificador.
CONCENTRATION_RANK: dict[Concentration, int] = {
    Concentration.COLOGNE: 1,
    Concentration.EDT: 2,
    Concentration.EDP: 3,
    Concentration.EXTRAIT: 4,
}


class Intention(str, Enum):
    ECOAR = "ecoar"
    SUAVIZAR = "suavizar"
    CONTRASTAR = "contrastar"
    CLAREAR = "clarear"
    ESCURECER = "escurecer"


class Occasion(str, Enum):
    DIA = "dia"
    NOITE = "noite"
    TRABALHO = "trabalho"
    ESPECIAL = "especial"
    CASUAL = "casual"


class Fragrance(Base):
    __tablename__ = "fragrances"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    brand: Mapped[str] = mapped_column(String(120))
    house_type: Mapped[HouseType] = mapped_column(SAEnum(HouseType, native_enum=False))
    gender: Mapped[Gender] = mapped_column(SAEnum(Gender, native_enum=False))
    concentration: Mapped[Concentration] = mapped_column(SAEnum(Concentration, native_enum=False))
    intensity: Mapped[int] = mapped_column(default=3)
    longevity_hours: Mapped[int] = mapped_column(default=6)

    primary_family: Mapped[OlfactoryFamily] = mapped_column(SAEnum(OlfactoryFamily, native_enum=False))
    secondary_family: Mapped[OlfactoryFamily | None] = mapped_column(
        SAEnum(OlfactoryFamily, native_enum=False), nullable=True
    )

    notes_top: Mapped[list[str]] = mapped_column(JSON, default=list)
    notes_heart: Mapped[list[str]] = mapped_column(JSON, default=list)
    notes_base: Mapped[list[str]] = mapped_column(JSON, default=list)

    best_season: Mapped[list[Season]] = mapped_column(SeasonListType, default=list)

    owned: Mapped[bool] = mapped_column(default=True)
    bottle_ml: Mapped[int] = mapped_column(default=100)
    ml_remaining: Mapped[int] = mapped_column(default=100)
    personal_rating: Mapped[int | None] = mapped_column(nullable=True)
    price_tier: Mapped[int] = mapped_column(default=2)

    notes_pessoais: Mapped[str] = mapped_column(Text, default="")

    combos_as_base: Mapped[list["LayeringCombo"]] = relationship(
        foreign_keys="LayeringCombo.base_fragrance_id", back_populates="base_fragrance"
    )
    combos_as_modifier: Mapped[list["LayeringCombo"]] = relationship(
        foreign_keys="LayeringCombo.modifier_fragrance_id", back_populates="modifier_fragrance"
    )


class LayeringCombo(Base):
    __tablename__ = "layering_combos"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), default="")

    base_fragrance_id: Mapped[int] = mapped_column(ForeignKey("fragrances.id"))
    modifier_fragrance_id: Mapped[int] = mapped_column(ForeignKey("fragrances.id"))

    intention: Mapped[Intention] = mapped_column(SAEnum(Intention, native_enum=False))
    compatibility_score: Mapped[int] = mapped_column(default=0)
    rationale: Mapped[str] = mapped_column(Text, default="")
    application_notes: Mapped[str] = mapped_column(Text, default="")

    best_season: Mapped[list[Season]] = mapped_column(SeasonListType, default=list)
    occasion: Mapped[Occasion] = mapped_column(SAEnum(Occasion, native_enum=False))

    user_rating: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[_dt.datetime] = mapped_column(
        default=lambda: _dt.datetime.now(_dt.timezone.utc)
    )

    base_fragrance: Mapped["Fragrance"] = relationship(
        foreign_keys=[base_fragrance_id], back_populates="combos_as_base"
    )
    modifier_fragrance: Mapped["Fragrance"] = relationship(
        foreign_keys=[modifier_fragrance_id], back_populates="combos_as_modifier"
    )


class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[_dt.date] = mapped_column(default=_dt.date.today)

    combo_id: Mapped[int | None] = mapped_column(ForeignKey("layering_combos.id"), nullable=True)
    fragrance_ids: Mapped[list[int]] = mapped_column(JSON, default=list)

    weather: Mapped[str] = mapped_column(String(120), default="")
    occasion: Mapped[Occasion] = mapped_column(SAEnum(Occasion, native_enum=False))
    mood_notes: Mapped[str] = mapped_column(Text, default="")
    rating: Mapped[int | None] = mapped_column(nullable=True)
    would_repeat: Mapped[bool] = mapped_column(default=True)

    combo: Mapped["LayeringCombo | None"] = relationship()
