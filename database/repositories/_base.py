"""Helpers compartilhados pelos repositories."""
from __future__ import annotations

from typing import Any, Iterable, Iterator, Mapping, Sequence

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

Row = Mapping[str, Any]

# O Postgres aceita no máximo 65535 parâmetros por query; os lotes ficam bem abaixo disso
DEFAULT_CHUNK = 1000


def chunks(items: Sequence[Row], size: int = DEFAULT_CHUNK) -> Iterator[Sequence[Row]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


def dedupe(rows: Iterable[Row], key: str) -> list[Row]:
    """Remove duplicatas pela chave (a última ocorrência vence).

    Necessário porque o ON CONFLICT não pode afetar a mesma linha duas vezes no mesmo comando.
    """
    return list({row[key]: row for row in rows}.values())


def check_same_keys(rows: Sequence[Row]) -> None:
    keys = set(rows[0])
    if any(set(r) != keys for r in rows):
        raise ValueError("Todas as linhas do lote precisam ter as mesmas chaves.")


def upsert(
    session: Session,
    model: type,
    rows: Sequence[Row],
    pk: str,
    immutable: tuple[str, ...] = (),
    refresh: Mapping[str, Any] | None = None,
) -> int:
    """INSERT ... ON CONFLICT (pk) DO UPDATE em lotes.

    immutable: colunas que nunca são sobrescritas no update (ex.: first_discovered_at)
    refresh:   colunas atualizadas sempre com um valor fixo/SQL (ex.: computed_at = now())
    """
    rows = dedupe(rows, pk)
    if not rows:
        return 0
    check_same_keys(rows)

    for chunk in chunks(rows):
        stmt = pg_insert(model).values(list(chunk))
        update_cols: dict[str, Any] = {
            col: stmt.excluded[col] for col in rows[0] if col != pk and col not in immutable
        }
        if refresh:
            update_cols.update(refresh)
        if update_cols:
            stmt = stmt.on_conflict_do_update(index_elements=[pk], set_=update_cols)
        else:
            stmt = stmt.on_conflict_do_nothing(index_elements=[pk])
        session.execute(stmt)
    return len(rows)
