"""Camada HTTP compartilhada para falar com a Roblox.

Usa curl_cffi com impersonate="chrome" porque o httpx travava
(ReadTimeout) nesses endpoints. Os endpoints são não documentados
e podem mudar.
"""

from __future__ import annotations

import time

from curl_cffi import requests

MAX_RETRIES = 4
TIMEOUT = 30
REQUEST_DELAY = 1.0  # pausa sugerida entre requisições (limite visto: 120/min)


def make_session() -> requests.Session:
    return requests.Session(impersonate="chrome")


def get_json(session: requests.Session, url: str, params: dict) -> dict:
    """GET com retry e backoff para 429 e erros 5xx."""
    espera = 2.0
    for tentativa in range(1, MAX_RETRIES + 1):
        resp = session.get(url, params=params, timeout=TIMEOUT)
        if resp.status_code == 429 or resp.status_code >= 500:
            if tentativa == MAX_RETRIES:
                resp.raise_for_status()
            retry_after = resp.headers.get("retry-after")
            time.sleep(float(retry_after) if retry_after else espera)
            espera *= 2
            continue
        resp.raise_for_status()
        return resp.json()
    raise RuntimeError("inalcançável")
