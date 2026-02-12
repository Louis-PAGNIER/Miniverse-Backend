# Utiliser Python 3.13 slim
FROM python:3.13-slim AS base

# Installer dépendances système minimales (psycopg2, sqlite, etc si besoin)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    sqlite3 \
    cron \
    dos2unix \
    && rm -rf /var/lib/apt/lists/*

# Installer Poetry
RUN pip install --no-cache-dir poetry

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers de config poetry
COPY pyproject.toml poetry.lock poetry.toml* ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-root --no-interaction --no-ansi

RUN useradd -u 1000 -m -U miniverse
RUN chown miniverse:miniverse /app

USER miniverse:miniverse

# Copier ton code
COPY app ./app

# Créer le dossier data (même si sera monté en volume au runtime)
RUN mkdir -p /app/data

# Exposer ton port (ex : Litestar sur 8000)
EXPOSE 8000

# Lancer ton serveur (adapté si tu utilises Litestar avec uvicorn)
CMD ["litestar", "--app", "app.main:app", "run", "--debug", "--host", "0.0.0.0", "--port", "8000"]
