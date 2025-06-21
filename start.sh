#!/bin/sh
python3 manage.py makemigrations backend, apps
python3 manage.py migrate

daphne backend.asgi:application -b 0.0.0.0 -p 80
