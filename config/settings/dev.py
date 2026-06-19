"""
Development / test settings.

Uses SQLite for zero-setup local verification and as the test database. This is
the settings module pytest points at (see pyproject.toml).
"""
from .base import *  # noqa: F401,F403
from .base import BASE_DIR

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# A non-secret key is fine for local development and tests.
SECRET_KEY = "django-insecure-dev-only-key-do-not-use-in-production"

# SECURITY WARNING: define the correct hosts in production!
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]

# Database — SQLite, zero setup.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

try:
    from .local import *  # noqa: F401,F403
except ImportError:
    pass
