"""CRUD de fragrâncias."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from layer.models import Fragrance
from layer.schemas import FragranceCreate, FragranceUpdate


def create_fragrance(session: Session, data: FragranceCreate) -> Fragrance:
    fragrance = Fragrance(**data.model_dump())
    session.add(fragrance)
    session.commit()
    session.refresh(fragrance)
    return fragrance


def list_fragrances(
    session: Session,
    *,
    owned: bool | None = None,
    primary_family: str | None = None,
    brand: str | None = None,
    best_season: str | None = None,
) -> list[Fragrance]:
    stmt = select(Fragrance)
    if owned is not None:
        stmt = stmt.where(Fragrance.owned == owned)
    if primary_family is not None:
        stmt = stmt.where(Fragrance.primary_family == primary_family)
    if brand is not None:
        stmt = stmt.where(Fragrance.brand == brand)
    stmt = stmt.order_by(Fragrance.brand, Fragrance.name)
    fragrances = list(session.execute(stmt).scalars().all())
    if best_season is not None:
        fragrances = [f for f in fragrances if best_season in [s.value for s in f.best_season]]
    return fragrances


def get_fragrance(session: Session, fragrance_id: int) -> Fragrance | None:
    return session.get(Fragrance, fragrance_id)


def update_fragrance(session: Session, fragrance_id: int, data: FragranceUpdate) -> Fragrance | None:
    fragrance = session.get(Fragrance, fragrance_id)
    if fragrance is None:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(fragrance, field, value)
    session.commit()
    session.refresh(fragrance)
    return fragrance


def delete_fragrance(session: Session, fragrance_id: int) -> bool:
    fragrance = session.get(Fragrance, fragrance_id)
    if fragrance is None:
        return False
    session.delete(fragrance)
    session.commit()
    return True


def low_stock_fragrances(session: Session, threshold_ml: int = 15) -> list[Fragrance]:
    """Fragrâncias com pouco líquido restante — usado no alerta de reposição (fase 2)."""
    stmt = select(Fragrance).where(Fragrance.owned == True, Fragrance.ml_remaining <= threshold_ml)  # noqa: E712
    return list(session.execute(stmt).scalars().all())
