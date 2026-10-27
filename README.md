# HROtrnding
Discover emerging trends across Roblox games.

Roblox Trend Radar is a data collection and trend analysis project designed to identify Roblox games that are rapidly gaining players.

Instead of focusing only on the most popular games, the project aims to track player growth over time, detect emerging games, and identify patterns among games with similar gameplay mechanics.

🎯 Project Goals

📈 Track player growth — Monitor changes in concurrent player counts over time.

🔎 Discover emerging games — Identify games that are gaining traction.

🧩 Detect emerging trends — Find patterns among games with similar gameplay mechanics.

📊 Analyze historical data — Compare game performance across different time periods.

## 🛠️ Tech Stack

Python — Core application and data processing.

HTTPX — HTTP requests to Roblox endpoints.

PostgreSQL — Planned storage for historical observations.

## ⚙️ Getting Started

Requirements

Python 3.10 or newer.

Git.

1. Clone the repository
```
git clone <repository-url>
cd roblox-trend-radar
```

2. Create a virtual environment

```
python -m venv .venv

```
Activate it on Linux or macOS:

```
source .venv/bin/activate
```
On Windows:

```
.venv\Scripts\Activate.ps1
```
3. Install dependencies
```
python -m pip install -r requirements.txt
```
4. Run the application
```
python main.py
```
# Roblox Trend Radar

Descubra tendências emergentes entre os jogos do Roblox.

O Roblox Trend Radar é um projeto de coleta de dados e análise de tendências para identificar jogos do Roblox que estão ganhando jogadores rapidamente. Em vez de olhar só para os mais populares, a ideia é acompanhar o crescimento de jogadores ao longo do tempo, detectar jogos emergentes e encontrar padrões entre jogos com mecânicas parecidas.

## 🎯 Objetivos

- 📈 **Acompanhar o crescimento de jogadores** — monitorar a variação de jogadores simultâneos ao longo do tempo.
- 🔎 **Descobrir jogos emergentes** — identificar jogos que estão ganhando tração.
- 🧩 **Detectar tendências** — encontrar padrões entre jogos com mecânicas semelhantes.
- 📊 **Analisar dados históricos** — comparar o desempenho dos jogos em períodos diferentes.

## 🚦 Status atual

| Parte | Status |
|---|---|
| Descoberta de jogos (`buscas/collector.py`) | ✅ Implementada |
| Consulta em lote por universe ID (`buscas/lookup.py`) | ✅ Implementada |
| Armazenamento em PostgreSQL | ⏳ Planejado |
| Análise de crescimento | ⏳ Planejado |
| Detecção de tendências / agrupamento de jogos | ⏳ Planejado |

## 🛠️ Stack

- **Python 3.10+** — aplicação e processamento de dados.
- **curl_cffi** — requisições HTTP aos endpoints da Roblox (veja [Por que curl_cffi e não httpx](#por-que-curl_cffi-e-não-httpx)).
- **PostgreSQL** — armazenamento planejado para o histórico de observações.

## 🗂️ Estrutura do projeto

```
.
├── buscas/
│   ├── collector.py     # Descobre jogos nas listas de descoberta da Roblox
│   ├── lookup.py        # Consulta detalhes de jogos em lote, por universe ID
│   └── roblox_http.py   # Camada HTTP compartilhada (sessão, retry, backoff)
├── requirements.txt
└── README.md
```

Cada módulo tem uma única responsabilidade. `collector.py` e `lookup.py` não dependem um do outro: os dois dependem só de `roblox_http.py`.

## ⚙️ Como funciona

```
 Listas de descoberta da Roblox       universe IDs          Detalhes dos jogos
      (sorts da Explore API)   ───►  (do collector, de  ───►    (API de games)
          collector.py               um banco, etc.)              lookup.py
```

1. **Descoberta** — o `collector.py` pergunta à Explore API quais jogos estão nas listas que a Roblox mostra na página inicial e devolve esses jogos sem repetição.
2. **Consulta** — o `lookup.py` recebe uma lista de universe IDs e devolve os detalhes atualizados de cada jogo, em lotes.

As duas etapas são independentes: o `lookup.py` pode ser chamado com IDs que vieram do coletor, de um banco ou de um arquivo.

## 📦 Módulos

### `buscas/collector.py` — descoberta de jogos

Função única: coletar jogos das listas de descoberta.

```python
from buscas.collector import collect_games

jogos = collect_games()
```

`collect_games(sorts=DEFAULT_SORTS)` devolve uma `list[DiscoveredGame]`, sem jogos repetidos.

**Listas (sorts) consultadas por padrão:** `top-trending`, `up-and-coming`, `top-playing-now`, `fun-with-friends`, `top-revisited`.

**Campos de `DiscoveredGame`**

| Campo | Descrição |
|---|---|
| `universe_id` | ID do universo do jogo (é o que se usa na consulta) |
| `root_place_id` | ID do place inicial do jogo |
| `name` | Nome do jogo |
| `player_count` | Jogadores simultâneos no momento da coleta |
| `up_votes` / `down_votes` | Total de votos positivos e negativos |
| `genre` | Gênero principal (`genreL1`) |
| `sources` | Listas em que o jogo apareceu |

### `buscas/lookup.py` — consulta em lote

Função única: consultar jogos já conhecidos pelo universe ID.

```python
from buscas.lookup import fetch_games

detalhes = fetch_games([10771421858, 10770728771])
```

`fetch_games(universe_ids)` devolve uma `list[GameDetails]`. IDs duplicados são removidos e as requisições são feitas em lotes de 50 IDs.

Jogos removidos, privados ou inexistentes **não voltam** na resposta. Para saber quais sumiram, compare os IDs retornados com os IDs enviados.

**Campos de `GameDetails`**

| Campo | Descrição |
|---|---|
| `universe_id` | ID do universo |
| `root_place_id` | ID do place inicial |
| `name` | Nome do jogo |
| `creator` | Nome do criador |
| `genre` | Gênero |
| `created` | Data de criação (UTC, com fuso) |
| `playing` | Jogadores simultâneos no momento da consulta |
| `visits` | Total de visitas |
| `favorites` | Total de favoritos |

> **Atenção:** use o **universe ID**, não o ID do place (`root_place_id`). O endpoint de consulta só entende universe IDs.

### `buscas/roblox_http.py` — camada HTTP compartilhada

- `make_session()` cria uma sessão do `curl_cffi` que imita o Chrome.
- `get_json(session, url, params)` faz um GET com retry e backoff exponencial para HTTP 429 e erros 5xx, respeitando o header `Retry-After` quando existe.
- `REQUEST_DELAY` (1 s) é a pausa usada entre requisições.

## 🚀 Como começar

### Requisitos

- Python 3.10 ou superior
- Git

### 1. Clone o repositório

```bash
git clone <url-do-repositorio>
cd roblox-trend-radar
```

### 2. Crie um ambiente virtual

```bash
python -m venv .venv
```

Ative no Linux ou macOS:

```bash
source .venv/bin/activate
```

No Windows:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Instale as dependências

```bash
python -m pip install -r requirements.txt
```

### 4. Execute os módulos

Rode sempre a partir da **raiz do projeto**, com `python -m`, porque os módulos usam imports relativos dentro do pacote `buscas`.

Coletar jogos (imprime o total e os 10 primeiros):

```bash
python3 -m buscas.collector
```

Consultar jogos por universe ID:

```bash
python3 -m buscas.lookup 10771421858 10770728771
```

Usar os dois juntos em outro arquivo, na raiz:

```python
from buscas.collector import collect_games
from buscas.lookup import fetch_games

descobertos = collect_games()
ids = [g.universe_id for g in descobertos]
detalhes = fetch_games(ids)
```

A coleta faz cerca de 5 requisições (uma por lista) e leva alguns segundos por causa da pausa de 1 s entre elas.

## ⚠️ Limitações e observações

### Endpoints não documentados

O projeto usa endpoints da Roblox que **não têm documentação oficial** e podem mudar sem aviso:

- `apis.roblox.com/explore-api/v1/get-sort-content` (listas de descoberta)
- `games.roblox.com/v1/games` (detalhes dos jogos)

As respostas podem mudar de formato ou parar de funcionar. Leia os [Termos de Uso da Roblox](https://rblx.co/TOU) antes de fazer coletas pesadas ou de publicar os dados coletados.

### Por que curl_cffi e não httpx

Requisições feitas com o `httpx` a esses endpoints travam com `ReadTimeout`, mesmo com a conexão e o handshake TLS completos e com a mesma URL respondendo em menos de um segundo no `curl`. Mudar headers, compressão, keep-alive ou a versão do HTTP não resolveu. Usar o `curl_cffi` com `impersonate="chrome"` resolveu, o que sugere que a causa é o fingerprint TLS do cliente. Essa é a melhor explicação encontrada até agora, não uma causa confirmada.

### Cobertura

O coletor só enxerga os jogos que a Roblox coloca nas listas de descoberta, e cada lista devolve uma quantidade fixa de jogos. Uma execução retornou 323 jogos únicos. Jogos pequenos ou muito novos que não estão em destaque não aparecem. Não existe endpoint oficial para listar todos os jogos da plataforma.

Note também que a lista `up-and-coming` seleciona jogos *publicados* nos últimos 28 dias, o que não é o mesmo que a data de criação devolvida pelo `lookup.py` (`created`).

### Limite de requisições

As respostas da Explore API informam um limite de 120 requisições por janela de 60 segundos (header `x-ratelimit-limit`). O projeto fica bem abaixo disso, com 1 segundo de pausa entre requisições e backoff automático em caso de HTTP 429.
