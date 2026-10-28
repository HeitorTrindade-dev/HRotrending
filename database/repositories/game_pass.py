from __future__ import annotations

from typing import Sequence

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from ..models import GamePass

from ._base import Row, upsert


class GamePassRepository:
    def __init__(self, session: Session):
        self.session = session

    def upsert_many(self, rows: Sequence[Row]) -> int:
        """Insere ou atualiza passes e renova `last_checked_at`."""
        return upsert(
            self.session, GamePass, rows, pk="pass_id", refresh={"last_checked_at": func.now()}
        )

    def list_by_game(self, universe_id: int, only_for_sale: bool = False) -> list[GamePass]:
        stmt = select(GamePass).where(GamePass.universe_id == universe_id)
        if only_for_sale:
            stmt = stmt.where(GamePass.is_for_sale.is_(True))
        return list(self.session.scalars(stmt.order_by(GamePass.price_robux)))

    def mark_unavailable(self, universe_id: int, keep_pass_ids: Sequence[int]) -> int:
        """Marca como fora de venda os passes do jogo que não vieram na última coleta."""
        stmt = (
            update(GamePass)
            .where(GamePass.universe_id == universe_id)
            .values(is_for_sale=False, price_robux=None, last_checked_at=func.now())
        )
        if keep_pass_ids:
            stmt = stmt.where(GamePass.pass_id.notin_(keep_pass_ids))
        return self.session.execute(stmt).rowcount

    def stats_by_game(self, universe_ids: Sequence[int] | None = None) -> dict[int, dict[str, float]]:
        """Agregados de monetização por jogo (alimenta as features de ML).

        Considera só passes à venda e com preço.
        """
        stmt = (
            select(
                GamePass.universe_id,
                func.count(GamePass.pass_id),
                func.avg(GamePass.price_robux),
                func.max(GamePass.price_robux),
            )
            .where(GamePass.is_for_sale.is_(True), GamePass.price_robux.is_not(None))
            .group_by(GamePass.universe_id)
        )
        if universe_ids is not None:
            stmt = stmt.where(GamePass.universe_id.in_(universe_ids))
        return {
            uid: {
                "total_gamepasses": total,
                "avg_gamepass_price": float(avg or 0),
                "max_gamepass_price": int(mx or 0),
            }
            for uid, total, avg, mx in self.session.execute(stmt)
        }
