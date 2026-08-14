#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input

if [ -z "$DATABASE_URL" ]; then
  echo "AVISO: DATABASE_URL vazio. Usando SQLite (nao recomendado no Render)."
  echo "Adicione DATABASE_URL no Web Service -> Environment -> Internal Database URL do Postgres."
fi

python manage.py migrate --no-input
python manage.py atualizar_site
