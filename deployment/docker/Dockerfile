# Stage 1: Builder
FROM python:3.11-slim as builder

RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app
COPY pyproject.toml poetry.lock* README.md ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --only=main --no-root

# Copy source code for development stage
COPY . .

# Stage 2: Production
FROM python:3.11-slim as production

# Install curl for healthcheck
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -r fastapi && useradd -r -g fastapi fastapi

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app
COPY --chown=fastapi:fastapi . .

USER fastapi

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["gunicorn", "src.presentation.main:app", "-c", "gunicorn.conf.py"]