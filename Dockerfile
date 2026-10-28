FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependências primeiro: o cache do Docker só é invalidado se o requirements.txt mudar
COPY requirements.txt .
RUN python -m pip install -r requirements.txt

COPY buscas ./buscas
COPY database ./database

# Roda como usuário comum, não como root
RUN useradd --create-home appuser && chown -R appuser /app
USER appuser

# Padrão: cria as tabelas e termina. Troque o comando quando houver um ponto de entrada.
CMD ["python", "-m", "database.database"]
