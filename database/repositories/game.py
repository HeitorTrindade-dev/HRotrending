from __future__ import annotations

from typing import Iterable, Sequence

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from ..models import Game

from ._base import Row, upsert


class GameRepository:
    def __init__(self, session: Session):
        self.session = session

    def get(self, universe_id: int) -> Game | None:
        return self.session.get(Game, universe_id)

    def upsert_many(self, rows: Sequence[Row]) -> int:
        """Insere ou atualiza jogos. `first_discovered_at` nunca é sobrescrito."""
        return upsert(
            self.session, Game, rows, pk="universe_id", immutable=("first_discovered_at",)
        )

    def upsert(self, row: Row) -> int:
        return self.upsert_many([row])

    def list_ids(self, only_active: bool = True) -> list[int]:
        stmt = select(Game.universe_id)
        if only_active:
            stmt = stmt.where(Game.is_active.is_(True))
        return list(self.session.scalars(stmt))

    def existing_ids(self, universe_ids: Iterable[int]) -> set[int]:
        """Dos ids informados, quais já existem no banco (útil para achar jogos novos)."""
        ids = list(universe_ids)
        if not ids:
            return set()
        return set(self.session.scalars(select(Game.universe_id).where(Game.universe_id.in_(ids))))

    def set_active(self, universe_ids: Sequence[int], active: bool) -> int:
        if not universe_ids:
            return 0
        result = self.session.execute(
            update(Game).where(Game.universe_id.in_(universe_ids)).values(is_active=active)
        )
        return result.rowcount
