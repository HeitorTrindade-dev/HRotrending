"""Repositories do projeto.

Os repositories NÃO fazem commit: quem controla a transação é quem chama
(normalmente via `with get_session() as session`).

Uso:
    with get_session() as session:
        repos = Repositories(session)
        repos.games.upsert_many(rows)
"""
from sqlalchemy.orm import Session

from .game import GameRepository
from .game_pass import GamePassRepository
from .ml_features import FeatureRepository
from .snapshot import SnapshotRepository

__all__ = [
    "GameRepository",
    "SnapshotRepository",
    "GamePassRepository",
    "FeatureRepository",
    "Repositories",
]


class Repositories:
    """Fachada: um objeto só com todos os repositories da mesma sessão."""

    def __init__(self, session: Session):
        self.session = session
        self.games = GameRepository(session)
        self.snapshots = SnapshotRepository(session)
        self.passes = GamePassRepository(session)
        self.features = FeatureRepository(session)
