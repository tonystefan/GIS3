#!/usr/bin/env bash
set -e

echo "==> Instalando dependências..."
pip install -r requirements.txt

echo "==> Aplicando migrações..."
python manage.py migrate --noinput

echo "==> Coletando arquivos estáticos..."
python manage.py collectstatic --noinput --clear

echo "==> Populando glossário têxtil (se vazio)..."
python manage.py seed_glossario

echo "==> Build concluído."
