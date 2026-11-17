# Imatge de l'aplicació per a l'entorn de proves (decisió 090; docs/entorn-de-proves.md).
# Mateixa versió de Python que el CI. Sense dependències de desenvolupament ni navegadors.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY pyproject.toml ./
COPY config ./config
COPY apps ./apps
RUN pip install ".[deploy]"

COPY . .

# Els estàtics es recullen a la imatge; els serveix el Caddy des d'un volum compartit. Les claus
# d'aquí només existeixen durant la construcció: no protegeixen res i no queden a la imatge.
RUN export FIELD_ENCRYPTION_KEYS="$(python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')" \
    && DJANGO_SETTINGS_MODULE=config.settings.staging \
    DJANGO_SECRET_KEY=nomes-per-construir \
    DATABASE_URL=postgres://ningu@localhost/cap \
    python manage.py collectstatic --noinput \
    && useradd --create-home --uid 1000 cris \
    && mkdir -p /app/var /app/staticfiles-compartits \
    && chown -R cris /app/var /app/staticfiles /app/staticfiles-compartits

USER cris
EXPOSE 8000
ENTRYPOINT ["/app/deploy/proves/entrypoint.sh"]
CMD ["web"]
