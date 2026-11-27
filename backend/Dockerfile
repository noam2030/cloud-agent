FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app
# Install dependencies first so Docker can cache this layer.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY app ./app

# Cloud Run tells the container which port to listen on through $PORT.
CMD ["sh", "-c", "uv run --no-sync uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
