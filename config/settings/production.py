"""
Production settings.

Hardened for deployment on Railway (Postgres + R2) behind Cloudflare. Everything
sensitive or environment-specific comes from environment variables set in the
Railway dashboard — nothing secret lives in this file. See .env.example for the
full manifest and DEPLOY.md for the runbook.

Dev/test settings (SQLite, local media, console email, DEBUG=True) live in dev.py
and are intentionally untouched by the hardening here.
"""
import os

import dj_database_url

from .base import *  # noqa: F401,F403
from .base import INSTALLED_APPS, MIDDLEWARE

DEBUG = False

# --- Secrets & hosts (from env) -------------------------------------------
# A freshly generated production key — NOT the dev one. The developer generates
# it (e.g. `python -c "from django.core.management.utils import
# get_random_secret_key as g; print(g())"`) and sets it in Railway.
SECRET_KEY = os.environ["SECRET_KEY"]

# Comma-separated hostnames, e.g. "childrenlearning.org,www.childrenlearning.org,
# <project>.up.railway.app". The Railway subdomain is needed while DNS is still
# being set up.
ALLOWED_HOSTS = [h for h in os.environ.get("ALLOWED_HOSTS", "").split(",") if h]

# CSRF needs the scheme, unlike ALLOWED_HOSTS. e.g.
# "https://childrenlearning.org,https://www.childrenlearning.org".
CSRF_TRUSTED_ORIGINS = [
    origin
    for origin in os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin
]

# Absolute base URL Wagtail uses in admin notifications (e.g. password-reset
# links). e.g. "https://childrenlearning.org" — no trailing slash, no "/admin".
WAGTAILADMIN_BASE_URL = os.environ.get("WAGTAILADMIN_BASE_URL", "")

# --- Database (Railway Postgres injects DATABASE_URL) ---------------------
# dj-database-url parses the connection string; conn_max_age keeps connections
# warm, conn_health_checks recycles dead ones.
DATABASES = {
    "default": dj_database_url.config(
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# --- TLS / proxy / security baseline --------------------------------------
# THE proxy gotcha: Railway and Cloudflare terminate TLS upstream, so Django
# sees plain HTTP. Without this header it never believes a request is already
# HTTPS, and SECURE_SSL_REDIRECT below redirect-loops forever. Pairs with
# Cloudflare SSL mode "Full (strict)" — do not remove.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# HSTS — intentionally conservative to start. It is sticky: once a browser sees
# the header it enforces HTTPS for the full max-age, so we begin with one hour
# and raise it once we're confident. `manage.py check --deploy` WILL warn that
# this isn't a year and that subdomains/preload are off — those warnings are
# expected. Raise SECURE_HSTS_SECONDS deliberately later, never just to silence
# the warning.
SECURE_HSTS_SECONDS = 3600
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

# --- Middleware: add SecurityMiddleware + WhiteNoise -----------------------
# base.py omits SecurityMiddleware (dev doesn't need it); production must have it
# first so the SSL redirect / HSTS / nosniff settings above take effect, with
# WhiteNoise immediately after so it can serve hashed static assets.
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    *MIDDLEWARE,
]

# django-storages needs to be installed for the S3/R2 backend.
INSTALLED_APPS = [*INSTALLED_APPS, "storages"]

# --- Storage: media -> R2, static -> WhiteNoise ---------------------------
# Media goes to Cloudflare R2 (S3-compatible). Static stays on WhiteNoise with
# hashed/manifested filenames so a deploy never serves stale CSS to visitors.
# R2 values are read with .get() so `collectstatic` / `check --deploy` don't
# require them to be set — the S3 backend is only instantiated when media is
# actually accessed at runtime.
STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "bucket_name": os.environ.get("R2_BUCKET_NAME", ""),
            "access_key": os.environ.get("R2_ACCESS_KEY_ID", ""),
            "secret_key": os.environ.get("R2_SECRET_ACCESS_KEY", ""),
            # R2's S3 endpoint: https://<account>.r2.cloudflarestorage.com
            "endpoint_url": os.environ.get("R2_ENDPOINT_URL", ""),
            # R2 ignores region but the SDK insists on one; "auto" is correct.
            "region_name": "auto",
            # Serve media from media.childrenlearning.org so URLs use the custom
            # domain rather than the raw R2 endpoint.
            "custom_domain": os.environ.get("R2_CUSTOM_DOMAIN", ""),
            # Public, unsigned URLs (no ?X-Amz-... query string).
            "querystring_auth": False,
            # R2 doesn't implement S3 ACLs; sending one errors.
            "default_acl": None,
            # Never clobber an existing key — Wagtail renditions are immutable.
            "file_overwrite": False,
        },
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# --- Email (admin password reset, via SMTP) -------------------------------
# So a locked-out admin can actually reset their password. Pointed at Migadu by
# the developer. Dev stays on the console backend.
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.environ.get("EMAIL_HOST", "")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "True").lower() == "true"
EMAIL_USE_SSL = os.environ.get("EMAIL_USE_SSL", "False").lower() == "true"
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "")
