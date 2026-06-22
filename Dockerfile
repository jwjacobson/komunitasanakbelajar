# Production image for Komunitas Anak Belajar (Railway). Full runbook: DEPLOY.md.
#
# We own the build with this Dockerfile rather than Nixpacks: Nixpacks' auto-
# generated install step (`pip install uv==$NIXPACKS_UV_VERSION`) expanded the
# version to empty and pip rejected it. Owning the build removes that synthesized
# step and lets us pin Python and install uv explicitly.
#
# Build flow:
#   deps          -> uv sync (cached on pyproject.toml + uv.lock)
#   collectstatic -> baked into the image (WhiteNoise manifest/hashing). Must run
#                    at BUILD, not pre-deploy: pre-deploy runs in a throwaway
#                    container whose filesystem the web process never sees.
#   migrate       -> pre-deploy step in railway.toml (writes to the external DB,
#                    not the image), so it is NOT here.
#   run           -> gunicorn on $PORT (CMD below).

FROM python:3.13-slim

# uv from the official image — NOT pip (pip-installing uv is what broke Nixpacks).
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# Put the project venv on PATH so python/gunicorn resolve to it without `uv run`.
ENV PATH="/app/.venv/bin:$PATH"

# Install dependencies first, in their own layer, so a code-only change doesn't
# reinstall everything. --no-install-project: the app isn't a package (tool.uv
# package = false); we only want its deps here.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Now the application code.
COPY . .

# Reconcile the environment with the project now that the code is present.
RUN uv sync --frozen --no-dev

# Bake hashed/manifested static files into the image. production.py reads R2/email
# via .get(), so only SECRET_KEY is required to import settings — pass a dummy
# (collectstatic touches no secrets, just the static pipeline).
RUN DJANGO_SETTINGS_MODULE=config.settings.production \
    SECRET_KEY=build-only-dummy \
    python manage.py collectstatic --noinput

# Drop privileges for the running app.
RUN useradd --create-home --uid 1000 appuser \
    && chown -R appuser:appuser /app
USER appuser

# Railway injects $PORT; default to 8000 for a plain `docker run`.
CMD ["sh", "-c", "gunicorn config.wsgi --bind 0.0.0.0:${PORT:-8000}"]
