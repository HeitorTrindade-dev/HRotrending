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
| Banco PostgreSQL: models, conexão e repositories (`database/`) | ✅ Implementado |
| Ligação coletor → banco (gravar o que é coletado) | ⏳ Planejado |
| Migrations (Alembic) | ⏳ Planejado |
| Cálculo das features (`ml_game_features`) | ⏳ Planejado |
| Detecção de tendências / agrupamento de jogos | ⏳ Planejado |

## 🛠️ Stack

- **Python 3.10+** — aplicação e processamento de dados.
- **curl_cffi** — requisições HTTP aos endpoints da Roblox (veja [Por que curl_cffi e não httpx](#por-que-curl_cffi-e-não-httpx)).
- **PostgreSQL** — armazenamento do histórico de observações.
- **SQLAlchemy 2** + **psycopg 3** — acesso ao banco.
- **python-dotenv** — configuração por variáveis de ambiente.

## 🗂️ Estrutura do projeto

```
.
├── buscas/
│   ├── collector.py         # Descobre jogos nas listas de descoberta da Roblox
│   ├── lookup.py            # Consulta detalhes de jogos em lote, por universe ID
│   └── roblox_http.py       # Camada HTTP compartilhada (sessão, retry, backoff)
├── database/
│   ├── models.py            # Tabelas (SQLAlchemy)
│   ├── database.py          # Engine, sessão e criação das tabelas (lê o .env)
│   └── repositories/
│       ├── _base.py         # Helpers compartilhados (upsert em lote)
│       ├── game.py          # games
│       ├── snapshot.py      # game_snapshots
│       ├── game_pass.py     # game_passes
│       └── ml_features.py   # ml_game_features
├── .env.example             # Modelo das variáveis de ambiente
├── Dockerfile               # Imagem do programa
├── docker-compose.yml       # PostgreSQL + programa
├── .dockerignore
├── requirements.txt
└── README.md
```

Cada módulo tem uma única responsabilidade. `buscas/` fala com a Roblox; `database/` fala com o PostgreSQL. Um não depende do outro.

## 🚀 Como começar

### Requisitos

- Python 3.10 ou superior
- PostgreSQL
- Git

### 1. Clone o repositório

```bash
git clone <url-do-repositorio>
cd HRotrending
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

### 4. Configure o banco

Crie o banco no PostgreSQL:

```bash
createdb roblox
```

Copie o modelo de variáveis e preencha com os seus dados:

```bash
cp .env.example .env
```

| Variável | Obrigatória | Padrão | Descrição |
|---|---|---|---|
| `POSTGRES_USER` | sim | — | Usuário do banco |
| `POSTGRES_PASSWORD` | sim | — | Senha do banco |
| `POSTGRES_DB` | sim | — | Nome do banco |
| `POSTGRES_HOST` | não | `localhost` | Host do PostgreSQL |
| `POSTGRES_PORT` | não | `5432` | Porta do PostgreSQL |
| `DB_POOL_SIZE` | não | `5` | Conexões mantidas abertas no pool |
| `DB_MAX_OVERFLOW` | não | `10` | Conexões extras permitidas em picos |
| `SQL_ECHO` | não | `0` | `1` imprime as queries SQL no console |

O `.env` está no `.gitignore` e **nunca deve ser commitado**. A URL de conexão é montada pelo código a partir dessas variáveis, então senhas com caracteres especiais (`@`, `:`, `/`) funcionam sem escape.

### 5. Crie as tabelas

Rode a partir da **raiz do projeto**:

```bash
python -m database.database
```

Isso cria as 4 tabelas (`CREATE TABLE IF NOT EXISTS`, então é seguro rodar mais de uma vez). Ele **não altera** tabelas que já existem: se o schema mudar, ainda é preciso recriar o banco ou aplicar a mudança à mão (veja [Migrations](#-limitações-e-observações)).

### Alternativa: rodando com Docker

Sobe o PostgreSQL e o programa juntos, sem instalar nada além do Docker.

```bash
cp .env.example .env        # preencha POSTGRES_USER, POSTGRES_PASSWORD e POSTGRES_DB
docker compose up --build
```

O que acontece:

1. O serviço `db` (PostgreSQL 16) sobe e só é considerado pronto depois de passar no healthcheck.
2. O serviço `app` é construído a partir do `Dockerfile`, espera o banco ficar saudável, cria as tabelas (`python -m database.database`) e **termina**. Isso é esperado: o projeto ainda não tem um ponto de entrada que fique rodando.
3. Os dados ficam no volume `pgdata` e sobrevivem a `docker compose down`.

Comandos úteis:

```bash
docker compose up -d db                              # só o banco (para rodar o Python na sua máquina)
docker compose run --rm app python -m database.database   # recria as tabelas que faltam
docker compose exec db psql -U <usuario> -d <banco>  # abre o psql
docker compose down                                  # para tudo, mantém os dados
docker compose down -v                               # para tudo e APAGA os dados
```

Observações:

- Dentro do Compose o programa fala com o banco pelo host `db`. O `POSTGRES_HOST` do `.env` só vale quando você roda o Python direto na sua máquina.
- `POSTGRES_PORT` define a porta exposta no seu computador (útil para DBeaver, `psql`, etc.). Se a 5432 já estiver ocupada, troque no `.env`.
- O PostgreSQL só lê usuário, senha e nome do banco na **primeira** vez que o volume é criado. Mudar esses valores no `.env` depois não altera um banco já existente; para recomeçar, use `docker compose down -v`.

## 🗄️ Banco de dados

### Tabelas

| Tabela | Tipo | Descrição |
|---|---|---|
| `games` | Dimensão | Um registro por jogo: criador, place inicial, data de criação, data da primeira descoberta e se ainda está ativo. |
| `game_snapshots` | Série temporal | Uma linha por jogo a cada coleta: jogadores simultâneos, visitas, favoritos, votos, gênero, em quais listas apareceu, nome e descrição. Só recebe inserts. |
| `game_passes` | Monetização | Game passes de cada jogo, com preço, se está à venda e quando foi verificado pela última vez. |
| `ml_game_features` | Feature store | Uma linha por jogo com features pré-calculadas para ML: crescimento, engajamento, monetização, mecânicas extraídas e cluster. |

Todas as tabelas filhas referenciam `games.universe_id` com `ON DELETE CASCADE`: apagar um jogo apaga seus snapshots, passes e features. `game_snapshots` tem índices em `(universe_id, collected_at)` e em `collected_at`, para as consultas de janela de tempo (24h, 7d).

> O schema usa `ARRAY` do PostgreSQL (`active_sorts`, `extracted_mechanics`). Ele **não funciona** em outros bancos como SQLite.

### Repositories

Os repositories ficam em `database/repositories/`, um arquivo por tabela, e são reunidos pela fachada `Repositories`:

```python
from datetime import datetime, timedelta, timezone

from database.database import get_session
from database.repositories import Repositories

with get_session() as session:
    repos = Repositories(session)

    repos.games.upsert_many([{
        "universe_id": 123,
        "root_place_id": 456,
        "creator_id": 1,
        "creator_name": "Studio X",
        "created_at_roblox": datetime(2025, 1, 1, tzinfo=timezone.utc),
    }])
    repos.snapshots.add({"universe_id": 123, "name": "Meu Jogo", "playing": 1500, "visits": 90000})

    ontem = datetime.now(timezone.utc) - timedelta(hours=24)
    antigo = repos.snapshots.at_or_before(123, ontem)   # CCU de 24h atrás
```

| Repository | Principais métodos |
|---|---|
| `games` | `upsert_many`, `get`, `list_ids`, `existing_ids`, `set_active` |
| `snapshots` | `add_many`, `latest`, `latest_per_game`, `at_or_before`, `series`, `avg_playing`, `count`, `prune_older_than` |
| `passes` | `upsert_many`, `list_by_game`, `mark_unavailable`, `stats_by_game` |
| `features` | `upsert_many`, `get`, `list_by_cluster`, `iter_all` |

**Regras de projeto**

- **Os repositories não fazem commit.** Quem controla a transação é `get_session()`, que faz commit ao final e rollback se der erro. Assim, uma coleta inteira entra ou sai junta.
- **Upserts** usam `INSERT ... ON CONFLICT` do PostgreSQL, em lotes de 1000. `games.first_discovered_at` nunca é sobrescrito; `game_passes.last_checked_at` e `ml_game_features.computed_at` são renovados a cada upsert.
- **Duplicatas no mesmo lote** são removidas antes do envio (a última vence), porque o PostgreSQL recusa o mesmo id duas vezes no mesmo comando.
- **Todas as linhas de um lote precisam ter as mesmas chaves**; senão, um `ValueError` é lançado, em vez de gravar `NULL` por engano.
- **Snapshots só recebem inserts.** Se `snapshot_date` não vier no dado, é preenchido com a data de `collected_at`.

## 📦 Módulos de coleta

### `buscas/collector.py` — descoberta de jogos

Função única: coletar jogos das listas de descoberta.

```python
from collector import collect_games

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
from lookup import fetch_games

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

### Como usar os módulos de coleta

Os módulos de `buscas/` importam `roblox_http` sem prefixo de pacote e **ainda não têm ponto de entrada** de linha de comando. Por isso, use-os em Python com a pasta `buscas/` no caminho de busca:

```bash
PYTHONPATH=buscas python -c "from collector import collect_games; print(len(collect_games()))"
```

A coleta faz cerca de 5 requisições (uma por lista) e leva alguns segundos por causa da pausa de 1 s entre elas.

## ⚠️ Limitações e observações

### Migrations

O projeto ainda não usa migrations. `python -m database.database` só cria tabelas que não existem. Enquanto não houver dados que valha preservar, dá para recriar o banco quando o schema mudar. Quando houver histórico acumulado, o próximo passo é adotar o Alembic.

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
