"""Engine, sessão e inicialização do banco SQLite local (`layer.db`)."""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from layer.models import Base

# Raiz do projeto (dois níveis acima deste arquivo: layer/db.py -> layer/ -> raiz).
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "layer.db"

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def init_db() -> None:
    """Cria as tabelas se ainda não existirem. Idempotente."""
    Base.metadata.create_all(engine)


def get_session() -> Session:
    """Nova sessão — quem chama é responsável por fechar/usar como contexto."""
    return SessionLocal()


@contextmanager
def session_scope() -> Iterator[Session]:
    """Sessão como context manager, com commit/rollback automático."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
