from __future__ import annotations

from typing import Iterator, Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import MLGameFeatures

from ._base import Row, upsert


class FeatureRepository:
    def __init__(self, session: Session):
        self.session = session

    def get(self, universe_id: int) -> MLGameFeatures | None:
        return self.session.get(MLGameFeatures, universe_id)

    def upsert_many(self, rows: Sequence[Row]) -> int:
        """Grava as features calculadas e renova `computed_at`."""
        return upsert(
            self.session,
            MLGameFeatures,
            rows,
            pk="universe_id",
            refresh={"computed_at": func.now()},
        )

    def list_by_cluster(self, cluster_id: int) -> list[MLGameFeatures]:
        return list(
            self.session.scalars(
                select(MLGameFeatures).where(MLGameFeatures.assigned_cluster_id == cluster_id)
            )
        )

    def iter_all(self, batch_size: int = 1000) -> Iterator[MLGameFeatures]:
        """Percorre todas as features em streaming (para montar o dataset de treino)."""
        stmt = select(MLGameFeatures).execution_options(yield_per=batch_size)
        yield from self.session.scalars(stmt)
