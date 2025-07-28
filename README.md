# Crypto Price Service - ETH/USDT FastAPI

Высоконагруженный FastAPI-сервис для получения данных по торговой паре ETH/USDT.

## Требования

- Docker 20.10+
- Docker Compose 2.0+
- Make (опционально)
- 4GB RAM минимум для базовой версии
- 8GB RAM для версии с мониторингом и масштабированием

## Быстрый старт

### Production режим (минимальная конфигурация)

```bash
# Клонировать репозиторий
git clone <repository-url>
cd crypto-price-service

# Сборка и запуск
docker-compose up -d

# Проверка статуса
docker-compose ps

# API будет доступен на http://localhost:8000/api/
```

### Development режим

```bash
# Запустить в dev режиме с hot reload
docker-compose -f docker-compose.dev.yml up

# API будет доступен на http://localhost:8000
```

## API Endpoints

- `GET /api/v1/prices/eth-usdt` - Текущая цена ETH/USDT
- `GET /health/liveness` - Проверка жизнеспособности
- `GET /health/readiness` - Проверка готовности
- `GET /metrics` - Prometheus метрики (порт 8001)

## Производительность

Минимальная конфигурация (1 контейнер, 8 воркеров) обеспечивает:
- 300+ одновременных подключений
- Response time < 1000ms при пиковой нагрузке
- До 500 req/s throughput

## Нагрузочное тестирование

```bash
# Установить hey
go install github.com/rakyll/hey@latest

# Тест с 300 одновременными подключениями
hey -n 10000 -c 300 http://localhost:8000/api/v1/prices/eth-usdt

# Длительный тест
hey -z 60s -c 300 http://localhost:8000/api/v1/prices/eth-usdt
```

## Конфигурация

Основные переменные окружения:

- `WORKERS` - количество Gunicorn workers (default: 8)
- `REDIS_URL` - URL для подключения к Redis
- `LOG_LEVEL` - уровень логирования (debug/info/warning/error)
- `CACHE_TTL` - TTL для L1 кэша в секундах (default: 5)

## Мониторинг

Production конфигурация включает полный стек мониторинга:

- **Prometheus**: http://localhost:9090 - сбор метрик
- **Grafana**: http://localhost:3000 (admin/admin) - визуализация метрик
- **Loki**: http://localhost:3100 - централизованное хранение логов
- **Promtail**: автоматический сбор логов из контейнеров

Метрики доступны на отдельном порту: http://localhost:8001/metrics

## Troubleshooting

### Высокая latency
1. Проверить логи: `docker-compose logs app`
2. Проверить CPU/Memory: `docker stats`
3. Увеличить количество workers или добавить реплики

### Connection refused при высокой нагрузке
```bash
# Увеличить лимиты системы
sudo sysctl -w net.core.somaxconn=65535
sudo sysctl -w net.ipv4.tcp_max_syn_backlog=65535
```

### Redis connection errors
```bash
docker-compose logs redis
docker-compose restart redis
```

## Архитектура

- Clean Architecture с разделением на слои
- Асинхронная обработка с AIOHTTP
- Многоуровневое кэширование (In-Memory L1 + Redis L2)
- Circuit Breaker для защиты от сбоев внешних API
- Retry механизм с exponential backoff

См. полную документацию в `docs/architecture.md`

## Структура проекта

```
src/
├── domain/           # Бизнес-логика и сущности
├── application/      # Use cases и интерфейсы
├── infrastructure/   # Внешние сервисы и адаптеры
├── presentation/     # API и web-слой
└── shared/          # Общие утилиты
```

## Разработка

### Запуск в dev режиме
```bash
make dev-up
```

### Запуск тестов
```bash
make test           # Unit тесты
make test-load      # Нагрузочные тесты
```

### Линтеры и форматирование
```bash
make lint           # Проверка кода
make format         # Форматирование кода
```