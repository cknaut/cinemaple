#!/usr/bin/env bash
# Build script for Render.com (and similar) free-tier deploy.
# Install deps, collect static files, run migrations.
# Run with: bash build.sh  (works even if execute bit is not set)

set -o errexit

python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate --noinput
