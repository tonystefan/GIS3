#!/usr/bin/env bash
# exit on error

pip install -r requirements.txt

python3 manage.py collectstatic --no-input
python3 manage.py migrate
npm install
npm start