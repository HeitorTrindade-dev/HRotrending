import os
from contextlib import contextmanager
from typing import Iterator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import Session, sessionmaker

load_dotenv()


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Variável de ambiente obrigatória não definida: {name}")
    return value


DATABASE_URL = URL.create(
    drivername="postgresql+psycopg",
    username=_require("POSTGRES_USER"),
    password=_require("POSTGRES_PASSWORD"),
    host=os.getenv("POSTGRES_HOST", "localhost"),
    port=int(os.getenv("POSTGRES_PORT", "5432")),
    database=_require("POSTGRES_DB"),
)

engine = create_engine(
    DATABASE_URL,
    pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
    max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "10")),
    pool_pre_ping=True,   # testa a conexão antes de usar
    pool_recycle=1800,    # recicla conexões a cada 30 min
    echo=os.getenv("SQL_ECHO", "0") == "1",
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


@contextmanager
def get_session() -> Iterator[Session]:
    """Sessão com commit automático e rollback em caso de erro.

    Uso:
        with get_session() as session:
            session.add(obj)
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    """Cria as tabelas. Útil em desenvolvimento; em produção use Alembic."""
    from .models import Base

    Base.metadata.create_all(engine)


if __name__ == "__main__":
    init_db()
    print("Tabelas criadas.")
