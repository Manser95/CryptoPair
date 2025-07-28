# gunicorn.conf.py - оптимизация для 300+ подключений
import multiprocessing
import os

# Расчет воркеров: оптимизировано для высокой нагрузки
# Для 500+ подключений увеличиваем до 12 воркеров
workers = int(os.environ.get('WORKERS', min(multiprocessing.cpu_count() * 3, 12)))
worker_class = "uvicorn.workers.UvicornWorker"

# Увеличенный лимит соединений на воркер  
# 500+ соединений / 12 воркеров = ~50 на воркер (с запасом ставим 2000)
worker_connections = 2000

# Сетевые настройки
bind = "0.0.0.0:8000"
backlog = 2048  # Очередь ожидающих соединений

# Performance tuning - оптимизировано для высокой нагрузки
max_requests = 2000  # Перезапуск воркера после N запросов
max_requests_jitter = 400  # Случайный разброс для предотвращения одновременного рестарта
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