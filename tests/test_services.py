"""Testes das camadas de serviço (CRUD, combos, diário) contra um SQLite em memória."""
from __future__ import annotations

import datetime as _dt

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from layer.domain.compatibility import evaluate_pair
from layer.models import Base
from layer.schemas import FragranceCreate, FragranceUpdate, JournalEntryCreate
from layer.services import combo_service, fragrance_service, journal_service


@pytest.fixture()
def session() -> Session:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    db_session = SessionLocal()
    yield db_session
    db_session.close()


def _fragrance_payload(**overrides) -> FragranceCreate:
    base = dict(
        name="Fragrância Teste", brand="Marca", house_type="nicho", gender="unissex",
        concentration="edp", intensity=3, longevity_hours=8,
        primary_family="amadeirado", secondary_family="ambar",
        notes_top=["bergamota"], notes_heart=["cedro"], notes_base=["âmbar"],
        best_season=["inverno"], owned=True, bottle_ml=100, ml_remaining=100,
        personal_rating=None, price_tier=2, notes_pessoais="",
    )
    base.update(overrides)
    return FragranceCreate(**base)


class TestFragranceService:
    def test_create_and_get(self, session: Session) -> None:
        created = fragrance_service.create_fragrance(session, _fragrance_payload())

        fetched = fragrance_service.get_fragrance(session, created.id)

        assert fetched is not None
        assert fetched.name == "Fragrância Teste"

    def test_list_filters_by_owned(self, session: Session) -> None:
        fragrance_service.create_fragrance(session, _fragrance_payload(name="Tenho", owned=True))
        fragrance_service.create_fragrance(session, _fragrance_payload(name="Não Tenho", owned=False))

        owned = fragrance_service.list_fragrances(session, owned=True)

        assert [f.name for f in owned] == ["Tenho"]

    def test_update_partial(self, session: Session) -> None:
        created = fragrance_service.create_fragrance(session, _fragrance_payload())

        updated = fragrance_service.update_fragrance(
            session, created.id, FragranceUpdate(personal_rating=5, ml_remaining=42)
        )

        assert updated is not None
        assert updated.personal_rating == 5
        assert updated.ml_remaining == 42
        assert updated.name == "Fragrância Teste"  # não alterado permanece

    def test_delete(self, session: Session) -> None:
        created = fragrance_service.create_fragrance(session, _fragrance_payload())

        deleted = fragrance_service.delete_fragrance(session, created.id)

        assert deleted is True
        assert fragrance_service.get_fragrance(session, created.id) is None

    def test_low_stock(self, session: Session) -> None:
        fragrance_service.create_fragrance(session, _fragrance_payload(name="Acabando", ml_remaining=5))
        fragrance_service.create_fragrance(session, _fragrance_payload(name="Cheio", ml_remaining=90))

        low = fragrance_service.low_stock_fragrances(session, threshold_ml=15)

        assert [f.name for f in low] == ["Acabando"]


class TestComboService:
    def test_get_suggestions_for_fragrance(self, session: Session) -> None:
        alvo = fragrance_service.create_fragrance(
            session, _fragrance_payload(name="Alvo", primary_family="amadeirado", intensity=3)
        )
        fragrance_service.create_fragrance(
            session, _fragrance_payload(name="Parceiro", primary_family="ambar", intensity=2)
        )

        suggestions = combo_service.get_suggestions_for_fragrance(session, alvo.id)

        assert len(suggestions) == 1
        assert suggestions[0].compatibility_score >= 80

    def test_get_seasonal_suggestions(self, session: Session) -> None:
        fragrance_service.create_fragrance(
            session, _fragrance_payload(name="Inverno A", primary_family="amadeirado", best_season=["inverno"])
        )
        fragrance_service.create_fragrance(
            session, _fragrance_payload(name="Inverno B", primary_family="ambar", best_season=["inverno"])
        )

        suggestions = combo_service.get_seasonal_suggestions(session, season="inverno")

        assert len(suggestions) == 1
        assert suggestions[0].compatibility_score >= 80

    def test_save_combo_persists(self, session: Session) -> None:
        a = fragrance_service.create_fragrance(
            session, _fragrance_payload(name="A", primary_family="amadeirado", intensity=3)
        )
        b = fragrance_service.create_fragrance(
            session, _fragrance_payload(name="B", primary_family="ambar", intensity=2)
        )
        from layer.schemas import FragranceRead

        suggestion = evaluate_pair(FragranceRead.model_validate(a), FragranceRead.model_validate(b))

        combo = combo_service.save_combo(session, suggestion, intention="ecoar", occasion="noite")

        assert combo.id is not None
        assert combo.compatibility_score == suggestion.compatibility_score

        combos = combo_service.list_combos(session)
        assert len(combos) == 1

    def test_rate_combo(self, session: Session) -> None:
        a = fragrance_service.create_fragrance(
            session, _fragrance_payload(name="A", primary_family="amadeirado")
        )
        b = fragrance_service.create_fragrance(
            session, _fragrance_payload(name="B", primary_family="ambar")
        )
        from layer.schemas import FragranceRead

        suggestion = evaluate_pair(FragranceRead.model_validate(a), FragranceRead.model_validate(b))
        combo = combo_service.save_combo(session, suggestion, intention="ecoar", occasion="noite")

        rated = combo_service.rate_combo(session, combo.id, 4)

        assert rated is not None
        assert rated.user_rating == 4


class TestJournalService:
    def test_add_and_list_entry(self, session: Session) -> None:
        entry_data = JournalEntryCreate(
            date=_dt.date(2026, 8, 20), fragrance_ids=[1], occasion="dia",
            weather="frio", mood_notes="produtivo", rating=4, would_repeat=True,
        )

        journal_service.add_entry(session, entry_data)
        entries = journal_service.list_entries(session)

        assert len(entries) == 1
        assert entries[0].occasion.value == "dia"

    def test_entries_for_date_range(self, session: Session) -> None:
        journal_service.add_entry(
            session, JournalEntryCreate(date=_dt.date(2026, 1, 10), occasion="dia")
        )
        journal_service.add_entry(
            session, JournalEntryCreate(date=_dt.date(2026, 8, 10), occasion="noite")
        )

        in_range = journal_service.entries_for_date_range(
            session, _dt.date(2026, 8, 1), _dt.date(2026, 8, 31)
        )

        assert len(in_range) == 1
        assert in_range[0].occasion.value == "noite"
