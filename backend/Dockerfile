# syntax=docker/dockerfile:1
#
# Backend image. Build context is ./backend
#
#   docker build -t haze21/joa-backend:latest ./backend
#
# One image serves both roles. The web Deployment runs the default CMD
# (gunicorn); the Celery Deployment overrides `command` to run a worker. They
# must share an image -- a worker executing a different build of the task code
# than the web process enqueued is a genuinely nasty class of bug.

# ---------------------------------------------------------------------------
# Builder: compile wheels in a throwaway stage so the runtime image carries no
# compilers or headers.
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copied on its own so a code change does not invalidate the dependency layer.
COPY requirements/ requirements/
RUN pip install --upgrade pip && pip install -r requirements/production.txt

# ---------------------------------------------------------------------------
# Runtime
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    DJANGO_SETTINGS_MODULE=config.settings.production

# libpq5 is the runtime half of libpq-dev; psycopg needs it, nothing else does.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv

# Run as a non-root user. A container that does not need root should not have
# it, and some clusters refuse to schedule pods that ask for it.
RUN useradd --create-home --uid 10001 appuser
WORKDIR /app

COPY --chown=appuser:appuser . .

# Collect static assets at build time so the running container never writes to
# its own filesystem. The values here are throwaway: production settings read
# them at import, and collectstatic touches neither the database nor the host.
RUN DJANGO_SECRET_KEY=build-time-only-not-a-real-secret \
    DJANGO_ALLOWED_HOSTS=localhost \
    SECURE_SSL_REDIRECT=False \
    DATABASE_URL=sqlite:////tmp/build.sqlite3 \
    python manage.py collectstatic --noinput --clear \
    && rm -f /tmp/build.sqlite3

USER appuser
EXPOSE 8000

# Two workers by default; scale with replicas rather than a huge worker count,
# so the scheduler can spread load across nodes.
CMD ["gunicorn", "config.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "3", \
     "--threads", "2", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
