#!/usr/bin/env bash
# exit on error

pip install -r requirements.txt
python3 manage.py migrate
python3 manage.py collectstatic --no-input
npm install
npm start