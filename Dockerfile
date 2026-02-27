FROM node:22-bookworm-slim AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ .
RUN npm run build

FROM python:3.12-slim-bookworm

WORKDIR /app/backend

RUN pip install --no-cache-dir uv

COPY backend/pyproject.toml ./pyproject.toml
RUN uv sync --no-dev

COPY backend/ .
COPY --from=frontend-builder /app/frontend/out ./app/frontend_static

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" || exit 1

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
