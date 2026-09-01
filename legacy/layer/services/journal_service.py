"""Diário de uso."""
from __future__ import annotations

import datetime as _dt

from sqlalchemy import select
from sqlalchemy.orm import Session

from layer.models import JournalEntry
from layer.schemas import JournalEntryCreate


def add_entry(session: Session, data: JournalEntryCreate) -> JournalEntry:
    entry = JournalEntry(**data.model_dump())
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry


def list_entries(session: Session) -> list[JournalEntry]:
    stmt = select(JournalEntry).order_by(JournalEntry.date.desc())
    return list(session.execute(stmt).scalars().all())


def entries_for_date_range(session: Session, start: _dt.date, end: _dt.date) -> list[JournalEntry]:
    stmt = (
        select(JournalEntry)
        .where(JournalEntry.date >= start, JournalEntry.date <= end)
        .order_by(JournalEntry.date.desc())
    )
    return list(session.execute(stmt).scalars().all())


def update_entry_rating(session: Session, entry_id: int, rating: int, would_repeat: bool) -> JournalEntry | None:
    entry = session.get(JournalEntry, entry_id)
    if entry is None:
        return None
    entry.rating = rating
    entry.would_repeat = would_repeat
    session.commit()
    session.refresh(entry)
    return entry
