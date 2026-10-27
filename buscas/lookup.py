"""Consulta em lote: busca os detalhes de jogos a partir dos universe_ids.

Única função deste módulo: consultar jogos já conhecidos.
Para descobrir jogos novos, use collector.py.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timezone

from roblox_http import REQUEST_DELAY, get_json, make_session

DETAILS_URL = "https://games.roblox.com/v1/games"
BATCH_SIZE = 50  # universeIds por requisição


@dataclass(frozen=True)
class GameDetails:
    universe_id: int
    root_place_id: int | None
    name: str
    creator: str | None
    genre: str | None
    created: datetime        # sempre com fuso UTC
    playing: int
    visits: int
    favorites: int


def _parse_created(valor: str) -> datetime:
    dt = datetime.fromisoformat(valor.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _to_details(bruto: dict) -> GameDetails:
    criador = bruto.get("creator") or {}
    return GameDetails(
        universe_id=bruto["id"],
        root_place_id=bruto.get("rootPlaceId"),
        name=bruto.get("name", ""),
        creator=criador.get("name"),
        genre=bruto.get("genre"),
        created=_parse_created(bruto["created"]),
        playing=bruto.get("playing", 0) or 0,
        visits=bruto.get("visits", 0) or 0,
        favorites=bruto.get("favoritedCount", 0) or 0,
    )


def fetch_games(universe_ids: list[int]) -> list[GameDetails]:
    """Consulta os jogos em lotes de 50.

    Jogos removidos, privados ou inexistentes não voltam na resposta.
    Para saber quais sumiram, compare com a lista de IDs enviada.
    """
    ids = list(dict.fromkeys(universe_ids))  # remove duplicados, mantém a ordem
    session = make_session()
    resultado: list[GameDetails] = []

    for i in range(0, len(ids), BATCH_SIZE):
        lote = ids[i : i + BATCH_SIZE]
        resp = get_json(
            session,
            DETAILS_URL,
            {"universeIds": ",".join(map(str, lote))},
        )
        resultado.extend(_to_details(b) for b in resp.get("data", []))
        time.sleep(REQUEST_DELAY)

    return resultado
