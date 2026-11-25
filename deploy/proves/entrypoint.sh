#!/bin/sh
# Arrencada dels contenidors del servidor de proves (decisions 090 i 099;
# docs/guies/servidor-de-proves-al-portatil.md).
#   web     migra, carrega les dades inventades si la base és buida i serveix amb gunicorn.
#   worker  la cua de tasques (correus i tasques periòdiques).
set -eu

case "${1:-web}" in
  web)
    python manage.py migrate --noinput
    # Només amb una base buida: si ja hi ha dades, `seed_demo_data` es nega i no toca res.
    if python manage.py seed_demo_data; then
      python manage.py shell -c "import deploy.proves.credencials as c; c.envia()"
    else
      echo "La base ja té dades: no es carreguen dades inventades."
    fi
    exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers "${GUNICORN_WORKERS:-2}" \
      --threads "${GUNICORN_THREADS:-1}" \
      --access-logfile - --forwarded-allow-ips '*'
    ;;
  worker)
    exec python manage.py procrastinate worker
    ;;
  *)
    exec "$@"
    ;;
esac
