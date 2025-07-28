# gunicorn.conf.py - оптимизация для 300+ подключений
import multiprocessing
import os

# Расчет воркеров: 2-4 x CPU cores
# Для 300+ подключений достаточно 8 воркеров на современном сервере
workers = int(os.environ.get('WORKERS', min(multiprocessing.cpu_count() * 2 + 1, 8)))
worker_class = "uvicorn.workers.UvicornWorker"

# Увеличенный лимит соединений на воркер
# 300 соединений / 8 воркеров = ~40 на воркер (с запасом ставим 1000)
worker_connections = 1000

# Сетевые настройки
bind = "0.0.0.0:8000"
backlog = 2048  # Очередь ожидающих соединений

# Performance tuning
max_requests = 1200  # Перезапуск воркера после N запросов
max_requests_jitter = 200  # Случайный разброс для предотвращения одновременного рестарта
preload_app = True  # Загрузка приложения до форка воркеров
worker_tmp_dir = "/dev/shm"  # RAM-диск для временных файлов

# Timeout конфигурация
timeout = 300  # Общий таймаут запроса
keepalive = 5  # Keep-alive соединения
graceful_timeout = 60  # Время для graceful shutdown

# Логирование
accesslog = "-"  # stdout
errorlog = "-"   # stderr
loglevel = os.environ.get('LOG_LEVEL', 'info')

# Статистика для мониторинга
statsd_host = os.environ.get('STATSD_HOST', None)
if statsd_host:
    statsd_prefix = "fastapi.crypto"