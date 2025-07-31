#!/bin/bash
set -e

# Установка значений по умолчанию
WORKERS=${WORKERS:-8}
LOG_LEVEL=${LOG_LEVEL:-info}

export PYTHONPATH=/app:$PYTHONPATH

echo "Starting Crypto API with Gunicorn + Uvicorn workers..."
echo "Workers: $WORKERS"
echo "Log level: $LOG_LEVEL"
echo "Cache TTL: ${CACHE_TTL_L1:-5} seconds"
echo "Cache size: ${CACHE_MAX_SIZE:-100000} entries"

# Запуск через Gunicorn с Uvicorn воркерами
exec gunicorn src.presentation.main:app \
    -c gunicorn.conf.py \
    --workers $WORKERS \
    --log-level $LOG_LEVEL