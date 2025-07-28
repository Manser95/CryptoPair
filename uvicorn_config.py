"""
Uvicorn configuration for local development only.
For production, use Gunicorn with Uvicorn workers:
    gunicorn src.presentation.main:app -c gunicorn.conf.py
    
Docker deployments automatically use Gunicorn via docker_entrypoint.sh
"""
import multiprocessing
import os

# Calculate optimal workers
cpu_count = multiprocessing.cpu_count()
workers = int(os.environ.get('WORKERS', min((2 * cpu_count) + 1, 16)))

# Uvicorn specific settings
bind = "0.0.0.0:8000"
worker_class = "uvicorn.workers.UvicornWorker"

# Performance settings
limit_concurrency = 1000  # Max concurrent connections
limit_max_requests = 10000  # Restart worker after N requests
backlog = 2048

# Timeouts
timeout_keep_alive = 5
timeout_notify = 30

# HTTP settings
h11_max_incomplete_event_size = 16384
ws_max_size = 16777216
ws_ping_interval = 20.0
ws_ping_timeout = 10.0

# Loop settings - use uvloop for better performance
loop = "uvloop"
http = "httptools"

# SSL/TLS (if needed)
ssl_keyfile = None
ssl_certfile = None
ssl_version = 2
ssl_cert_reqs = 0
ssl_ca_certs = None

# Logging
access_log = True
log_level = os.environ.get('LOG_LEVEL', 'info').lower()

# Server header
server_header = False  # Hide server header for security
date_header = True

# Interface
interface = "asgi3"
lifespan = "on"

# For direct uvicorn run
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.presentation.main:app",
        host="0.0.0.0",
        port=8000,
        workers=workers,
        loop="uvloop",
        http="httptools",
        limit_concurrency=limit_concurrency,
        limit_max_requests=limit_max_requests,
        backlog=backlog,
        timeout_keep_alive=timeout_keep_alive,
        log_level=log_level,
        access_log=access_log,
        server_header=server_header,
    )