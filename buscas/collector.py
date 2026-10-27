"""Coletor: descobre jogos nas listas (sorts) da Roblox.

Única função deste módulo: coletar jogos.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass

from roblox_http import REQUEST_DELAY, get_json, make_session

EXPLORE_URL = "https://apis.roblox.com/explore-api/v1/get-sort-content"

DEFAULT_SORTS = (
    "top-trending",
    "up-and-coming",
    "top-playing-now",
    "fun-with-friends",
    "top-revisited",
)


@dataclass(frozen=True)
class DiscoveredGame:
    universe_id: int
    root_place_id: int | None
    name: str
    player_count: int
    up_votes: int
    down_votes: int
    genre: str | None
    sources: tuple[str, ...]   # listas em que o jogo apareceu


def collect_games(sorts: tuple[str, ...] = DEFAULT_SORTS) -> list[DiscoveredGame]:
    """Coleta os jogos das listas e devolve sem repetição."""
    session = make_session()
    session_id = str(uuid.uuid4())

    jogos: dict[int, dict] = {}       # universe_id -> dados do primeiro sort visto
    origens: dict[int, set[str]] = {}

    for sort_id in sorts:
        data = get_json(
            session,
            EXPLORE_URL,
            {
                "sessionId": session_id,
                "sortId": sort_id,
                "device": "computer",
                "country": "all",
            },
        )
        for g in data.get("games", []):
            uid = g["universeId"]
            jogos.setdefault(uid, g)
            origens.setdefault(uid, set()).add(sort_id)
        time.sleep(REQUEST_DELAY)

    return [
        DiscoveredGame(
            universe_id=uid,
            root_place_id=g.get("rootPlaceId"),
            name=g.get("name", ""),
            player_count=g.get("playerCount", 0) or 0,
            up_votes=g.get("totalUpVotes", 0) or 0,
            down_votes=g.get("totalDownVotes", 0) or 0,
            genre=g.get("genreL1"),
            sources=tuple(sorted(origens[uid])),
        )
        for uid, g in jogos.items()
    ]
