"""Geração e persistência de combinações de layering.

Ponte entre a camada de domínio pura (`domain.compatibility`, que não sabe
nada sobre banco de dados) e o banco: converte `Fragrance` (ORM) em
`FragranceRead` (Pydantic) para alimentar o motor, e persiste o resultado
escolhido pelo usuário como `LayeringCombo`.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from layer.domain.compatibility import ComboSuggestion, suggest_combos, suggest_from_scratch
from layer.models import Fragrance, LayeringCombo
from layer.schemas import FragranceRead


def _collection_as_schemas(session: Session) -> list[FragranceRead]:
    fragrances = session.execute(select(Fragrance)).scalars().all()
    return [FragranceRead.model_validate(f) for f in fragrances]


def get_suggestions_for_fragrance(session: Session, fragrance_id: int, top_n: int = 5) -> list[ComboSuggestion]:
    collection = _collection_as_schemas(session)
    return suggest_combos(fragrance_id, collection, top_n=top_n)


def get_suggestions_from_scratch(
    session: Session,
    intention: str,
    occasion: str | None = None,
    season: str | None = None,
    top_n: int = 10,
) -> list[ComboSuggestion]:
    collection = _collection_as_schemas(session)
    return suggest_from_scratch(collection, intention=intention, occasion=occasion, season=season, top_n=top_n)


def save_combo(
    session: Session,
    suggestion: ComboSuggestion,
    intention: str,
    occasion: str,
    name: str | None = None,
) -> LayeringCombo:
    """Persiste uma sugestão que o usuário decidiu guardar."""
    combo_name = name or f"{suggestion.base_fragrance.name} + {suggestion.modifier_fragrance.name}"
    combo = LayeringCombo(
        name=combo_name,
        base_fragrance_id=suggestion.base_fragrance.id,
        modifier_fragrance_id=suggestion.modifier_fragrance.id,
        intention=intention,
        compatibility_score=suggestion.compatibility_score,
        rationale=suggestion.rationale,
        application_notes=suggestion.application_notes,
        best_season=suggestion.best_season,
        occasion=occasion,
    )
    session.add(combo)
    session.commit()
    session.refresh(combo)
    return combo


def list_combos(session: Session) -> list[LayeringCombo]:
    stmt = select(LayeringCombo).order_by(LayeringCombo.created_at.desc())
    return list(session.execute(stmt).scalars().all())


def rate_combo(session: Session, combo_id: int, rating: int) -> LayeringCombo | None:
    combo = session.get(LayeringCombo, combo_id)
    if combo is None:
        return None
    combo.user_rating = rating
    session.commit()
    session.refresh(combo)
    return combo
