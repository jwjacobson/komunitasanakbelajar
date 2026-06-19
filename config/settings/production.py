"""
Production settings.

The database path is wired now (PostgreSQL via dj-database-url) per SPEC §10,
but Phase 1 does not require a running Postgres. Media storage (Cloudflare R2),
WhiteNoise static handling and gunicorn runtime wiring are Phase 3 — declared
in pyproject.toml but intentionally not configured here yet.
"""
import os

import dj_database_url

from .base import *  # noqa: F401,F403

DEBUG = False

# Read secrets / host config from the environment (Railway, see SPEC §10).
SECRET_KEY = os.environ["SECRET_KEY"]

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "").split(",")

CSRF_TRUSTED_ORIGINS = [
    origin
    for origin in os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin
]

# Database — PostgreSQL via DATABASE_URL (Railway managed plugin). dj-database-url
# parses the connection string; conn_max_age keeps connections warm.
DATABASES = {
    "default": dj_database_url.config(
        conn_max_age=600,
        conn_health_checks=True,
    )
}

WAGTAILADMIN_BASE_URL = os.environ.get("WAGTAILADMIN_BASE_URL", "")

# --- Phase 3 (not wired this phase) ---------------------------------------
# Media -> Cloudflare R2 via django-storages[s3] (SPEC §8); static -> WhiteNoise
# with manifest storage (SPEC §3). These are deliberately left unconfigured in
# Phase 1; the dependencies are already declared in pyproject.toml.
