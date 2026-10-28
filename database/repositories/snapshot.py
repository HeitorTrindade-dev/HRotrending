from __future__ import annotations

from datetime import date, datetime
from typing import Any, Sequence

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from models import GameSnapshot

from ._base import Row, check_same_keys, chunks


class SnapshotRepository:
    """Série temporal: só insere, nunca atualiza."""

    def __init__(self, session: Session):
        self.session = session

    def add_many(self, rows: Sequence[Row]) -> int:
        """Insere snapshots em lote. Preenche `snapshot_date` se não vier no dado."""
        if not rows:
            return 0
        prepared: list[dict[str, Any]] = []
        for row in rows:
            data = dict(row)
            if data.get("snapshot_date") is None:
                collected = data.get("collected_at")
                data["snapshot_date"] = collected.date() if collected else date.today()
            prepared.append(data)
        check_same_keys(prepared)
        for chunk in chunks(prepared, 500):
            self.session.execute(pg_insert(GameSnapshot).values(list(chunk)))
        return len(prepared)

    def add(self, row: Row) -> int:
        return self.add_many([row])

    def latest(self, universe_id: int) -> GameSnapshot | None:
        return self.session.scalars(
            select(GameSnapshot)
            .where(GameSnapshot.universe_id == universe_id)
            .order_by(GameSnapshot.collected_at.desc())
            .limit(1)
        ).first()

    def latest_per_game(self, universe_ids: Sequence[int] | None = None) -> list[GameSnapshot]:
        """Snapshot mais recente de cada jogo (DISTINCT ON do Postgres)."""
        stmt = (
            select(GameSnapshot)
            .distinct(GameSnapshot.universe_id)
            .order_by(GameSnapshot.universe_id, GameSnapshot.collected_at.desc())
        )
        if universe_ids is not None:
            stmt = stmt.where(GameSnapshot.universe_id.in_(universe_ids))
        return list(self.session.scalars(stmt))

    def at_or_before(self, universe_id: int, moment: datetime) -> GameSnapshot | None:
        """Último snapshot até determinado momento (ex.: o CCU de 24h atrás)."""
        return self.session.scalars(
            select(GameSnapshot)
            .where(GameSnapshot.universe_id == universe_id, GameSnapshot.collected_at <= moment)
            .order_by(GameSnapshot.collected_at.desc())
            .limit(1)
        ).first()

    def series(
        self,
        universe_id: int,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int | None = None,
    ) -> list[GameSnapshot]:
        """Série temporal de um jogo, em ordem cronológica."""
        stmt = select(GameSnapshot).where(GameSnapshot.universe_id == universe_id)
        if since:
            stmt = stmt.where(GameSnapshot.collected_at >= since)
        if until:
            stmt = stmt.where(GameSnapshot.collected_at <= until)
        stmt = stmt.order_by(GameSnapshot.collected_at.asc())
        if limit:
            stmt = stmt.limit(limit)
        return list(self.session.scalars(stmt))

    def avg_playing(self, universe_id: int, since: datetime) -> float | None:
        return self.session.scalar(
            select(func.avg(GameSnapshot.playing)).where(
                GameSnapshot.universe_id == universe_id, GameSnapshot.collected_at >= since
            )
        )

    def count(self, universe_id: int | None = None) -> int:
        stmt = select(func.count(GameSnapshot.snapshot_id))
        if universe_id is not None:
            stmt = stmt.where(GameSnapshot.universe_id == universe_id)
        return self.session.scalar(stmt) or 0

    def prune_older_than(self, cutoff: datetime) -> int:
        """Apaga snapshots antigos (retenção de dados)."""
        return self.session.execute(
            delete(GameSnapshot).where(GameSnapshot.collected_at < cutoff)
        ).rowcount
