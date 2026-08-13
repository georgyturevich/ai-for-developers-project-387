# Syntax: https://docs.docker.com/build/building/best-practices/

# ---- build stage: TypeSpec compiler + frontend build (Node 22, matching CI) ----
FROM node:22-slim AS build

WORKDIR /repo

# Root deps: the TypeSpec compiler lives here; `frontend/api:types` invokes it.
COPY package.json package-lock.json ./
RUN npm ci

# Frontend deps, then the source + contract, then the production build.
# VITE_API_URL="" makes the API client fall through to same-origin relative
# requests (see docs/adr/0006), so the frontend source stays byte-identical.
COPY frontend/package.json frontend/package-lock.json ./frontend/
RUN cd frontend && npm ci

COPY main.tsp tspconfig.yaml ./
COPY frontend ./frontend
RUN cd frontend && VITE_API_URL="" npm run build

# ---- runtime stage: FastAPI serving the API + the built SPA ----
FROM python:3.14-slim AS runtime

ENV UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# The Owner timezone (ADR-0003) resolves through ZoneInfo, which needs the tz
# database — the slim base image does not ship it.
RUN apt-get update \
    && apt-get install -y --no-install-recommends tzdata \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.11.31 /uv /usr/local/bin/uv
COPY --from=ghcr.io/astral-sh/uv:0.11.31 /uvx /usr/local/bin/uvx

# uv sync pulls the dev group by default — exclusion must be explicit. The
# project wheel needs the source present, so it ships in the same layer.
COPY backend/pyproject.toml backend/uv.lock ./
COPY backend/src ./src
RUN uv sync --frozen --no-group dev

COPY --from=build /repo/frontend/dist ./static

ENV STATIC_DIR=/app/static

EXPOSE 8000

# The venv's uvicorn, binding all interfaces on the platform-provided port.
# Exactly one worker: the in-memory store's atomicity assumes a single event
# loop (ADR-0004).
CMD ["sh", "-c", "uvicorn cal_bookings.app:create_app --factory --host 0.0.0.0 --port ${PORT:-8000}"]
