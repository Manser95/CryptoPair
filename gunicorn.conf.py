# gunicorn.conf.py - оптимизация для высокой производительности
import multiprocessing
import os

# Воркеры берутся из переменной окружения WORKERS (задается в docker_entrypoint.sh)
# Если WORKERS не задан в entrypoint, используем оптимальную формулу
if 'WORKERS' not in os.environ:
    cpu_count = multiprocessing.cpu_count()
    workers = min((2 * cpu_count) + 1, 16)

# Обязательно используем Uvicorn воркеры для асинхронности
worker_class = "uvicorn.workers.UvicornWorker"

# Увеличенный лимит соединений на воркер  
# Для асинхронных воркеров можно держать много соединений
worker_connections = 10000

# Сетевые настройки
bind = "0.0.0.0:8000"
backlog = 2048  # Очередь ожидающих соединений

# Performance tuning - максимальная производительность
max_requests = 10000  # Увеличиваем до 10k запросов
max_requests_jitter = 1000  # Случайный разброс
preload_app = True  # Загрузка приложения до форка воркеров
worker_tmp_dir = "/dev/shm"  # RAM-диск для временных файлов

# Timeout конфигурация - сокращаем таймауты
timeout = 30  # Снижаем общий таймаут до 30 секунд
keepalive = 2  # Keep-alive 2 секунды
graceful_timeout = 30  # Время для graceful shutdown

# Логирование
accesslog = "-"  # stdout
errorlog = "-"   # stderr
loglevel = os.environ.get('LOG_LEVEL', 'info')

# Статистика для мониторинга
statsd_host = os.environ.get('STATSD_HOST', None)
if statsd_host:
    statsd_prefix = "fastapi.crypto"