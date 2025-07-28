# Crypto Pairs API - High-Performance FastAPI Service

Высоконагруженный FastAPI-сервис для получения данных по криптовалютным парам с поддержкой ETH/USDT.

## Особенности

- ⚡ Высокая производительность (500+ RPS)
- 🚀 Gunicorn с Uvicorn workers для асинхронной обработки
- 🔄 Кэширование L1 in-memory
- 🛡️ Circuit breaker для защиты от каскадных сбоев
- 📊 Встроенный мониторинг (Prometheus + Grafana + Loki)
- 🔍 Полная трассировка запросов с correlation ID
- 🏗️ Clean Architecture для легкой поддержки и расширения
- 🐳 Полная контейнеризация с Docker

## Требования

**Минимальные (для новых разработчиков):**
- Docker 20.10+
- Docker Compose 2.0+
- Make
- 4GB RAM минимум

**Для разработки:**
- Python 3.11+
- Poetry (для локальной разработки)
- 8GB RAM для версии с мониторингом

## Быстрый старт

### Production режим с мониторингом

```bash
# Клонировать репозиторий
git clone <repository-url>
cd cryptopair

# Сборка и запуск всех сервисов
make up

# Или вручную:
docker-compose up -d

# Проверка статуса
make ps
# или
docker-compose ps

# API будет доступен на:
# - API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
# - Prometheus: http://localhost:9090
# - Grafana: http://localhost:3000 (admin/admin)
# - Loki: http://localhost:3100
```

### Development режим

```bash
# Запустить в dev режиме с hot reload
make dev-up

# Или вручную:
docker-compose -f docker-compose.dev.yml up

# API будет доступен на http://localhost:8000

# Просмотр логов
make dev-logs

# Остановка
make dev-down
```

## API Endpoints

### Основные endpoints

- `GET /api/v1/prices/{symbol}-{vs_currency}` - Получить текущую цену пары
- `GET /api/v1/prices/eth-usdt` - Shortcut для ETH/USDT пары  
- `GET /` - Информация об API
- `GET /docs` - Swagger UI документация
- `GET /redoc` - ReDoc документация

### Health checks

- `GET /health` - Общая проверка здоровья
- `GET /health/liveness` - Проверка жизнеспособности сервиса
- `GET /health/readiness` - Проверка готовности (включая зависимости)

### Мониторинг

- `GET /metrics` - Prometheus метрики

### Примеры запросов

```bash
# Получить цену ETH/USDT
curl http://localhost:8000/api/v1/prices/eth-usdt

# Получить цену BTC/USD
curl http://localhost:8000/api/v1/prices/btc-usd

# Проверить здоровье сервиса
curl http://localhost:8000/health/readiness
```

### Формат ответа

```json
{
  "symbol": "eth",
  "vs_currency": "usdt",
  "price": 3886.69,
  "volume_24h": 29306409998.70,
  "price_change_24h": 1.71,
  "last_updated": "2025-07-28T11:01:41",
  "pair": "ETH/USDT"
}
```

## Производительность

Минимальная конфигурация (1 контейнер, 8 воркеров) обеспечивает:
- 300+ одновременных подключений
- Response time < 1000ms при пиковой нагрузке
- До 500 req/s throughput

## Тестирование

### 🚀 Быстрый старт для новых разработчиков

**Требования:** только Docker, Docker Compose и Make

```bash
# 1. Клонировать и перейти в проект
git clone <repository-url>
cd cryptopair

# 2. Запустить автоматическую настройку
make setup-test
```

**Готово!** Команда автоматически все настроит и запустит тесты.

📖 **Подробное руководство:** см. [TESTING.md](TESTING.md)

### Запуск тестов в Docker (рекомендуется)

```bash
# Запустить все тесты в изолированном Docker окружении
make test-docker

# CI/CD режим (подходит для автоматизации)
make test-ci
```

### Запуск тестов в работающем приложении

Если приложение уже запущено (`make up`):

```bash
# Запустить все тесты
make test

# Только unit тесты
make test-unit

# Только integration тесты  
make test-integration

# Тесты с покрытием
make test-all
```

### Нагрузочное тестирование

```bash
# Тест с hey (300 одновременных подключений)
make test-load

# Стресс-тест на 60 секунд
make test-stress

# k6 тест (требует установки k6)
make k6-test

# Locust тест с Web UI (требует запущенного приложения)
make up  # Сначала запустить приложение
make locust-test  # Затем нагрузочный тест
# UI доступен на http://localhost:8089

# Полный benchmark suite (Python-based, требует запущенного приложения)
make up  # Сначала запустить приложение
make benchmark  # Затем benchmark

# Быстрый benchmark
make benchmark-quick
```

## Конфигурация

Основные переменные окружения:

### Приложение
- `WORKERS` - количество Gunicorn workers (default: 8)
- `LOG_LEVEL` - уровень логирования (DEBUG/INFO/WARNING/ERROR, default: INFO)
- `LOG_FORMAT` - формат логов (json/text, default: json)
- `ENABLE_METRICS` - включить Prometheus метрики (default: true)
- `RELOAD` - hot reload для dev режима (default: false)

### Кэширование
- `CACHE_TTL` - TTL для L1 кэша в секундах (default: 5)
- `CACHE_MAX_SIZE_L1` - максимальный размер L1 кэша (default: 1000)

### Внешние API
- `COINGECKO_API_KEY` - API ключ для CoinGecko Pro (опционально)
- `COINGECKO_BASE_URL` - базовый URL CoinGecko API

### Circuit Breaker
- `CIRCUIT_BREAKER_FAILURE_THRESHOLD` - порог ошибок (default: 5)
- `CIRCUIT_BREAKER_RECOVERY_TIMEOUT` - таймаут восстановления в секундах (default: 60)
- `CIRCUIT_BREAKER_EXPECTED_EXCEPTION` - ожидаемые исключения

## Мониторинг

### Метрики

Сервис предоставляет следующие метрики в формате Prometheus:

- `http_requests_total` - Общее количество HTTP запросов
- `http_request_duration_seconds` - Время обработки запросов
- `cache_hits_total` / `cache_misses_total` - Статистика кеша
- `external_api_requests_total` - Запросы к внешним API
- `circuit_breaker_state` - Состояние circuit breaker
- `active_connections` - Активные соединения

### Логирование

Все логи выводятся в JSON формате с поддержкой correlation ID для трассировки запросов:

```json
{
  "asctime": "2025-07-28 11:01:41",
  "name": "src.application.use_cases.get_price",
  "levelname": "INFO",
  "message": "Fetched and cached price for eth/usdt",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

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


## Архитектура

### Основные компоненты

- **Clean Architecture** с четким разделением на слои
- **Асинхронная обработка** с использованием AIOHTTP для высокой производительности  
- **Многоуровневое кэширование**:
  - L1 (In-Memory) - 3 секунды TTL для быстрого доступа
  - Оптимизированный cache service с предзагрузкой популярных пар
- **Circuit Breaker** для защиты от каскадных сбоев (порог: 5 ошибок)
- **Retry механизм** с exponential backoff (до 5 попыток)
- **Rate limiting** на стороне клиента для соблюдения лимитов API
- **Health checks** с детальной информацией о состоянии компонентов
- **Correlation ID** для сквозной трассировки запросов

### Интеграция с CoinGecko

Для пар криптовалют (например, ETH/USDT) сервис:
1. Получает цены обеих валют в USD
2. Вычисляет кросс-курс
3. Кеширует результат

См. полную документацию в `tech_spec_arch.md`

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

### Использование Makefile

```bash
# Основные команды
make help               # Показать все доступные команды
make build              # Собрать Docker образы
make up                 # Запустить все сервисы
make down               # Остановить сервисы
make logs               # Показать логи
make health             # Проверить здоровье сервисов

# Разработка
make dev-up             # Запустить в dev режиме
make dev-down           # Остановить dev режим
make shell              # Доступ к shell контейнера

# Тестирование
make test               # Запустить все тесты
make test-unit          # Запустить unit тесты
make test-integration   # Запустить integration тесты
make test-load          # Запустить нагрузочные тесты

# Качество кода
make lint               # Проверить код линтерами
make format             # Отформатировать код

# Мониторинг
make grafana            # Открыть Grafana
make prometheus         # Открыть Prometheus
make loki               # Информация о Loki

# Управление
make scale N=3          # Масштабировать до 3 инстансов
make restart SERVICE=app # Перезапустить сервис
make clean              # Очистить контейнеры и volumes
```

### Установка зависимостей локально

```bash
# С pip
make install-deps

# С Poetry
make poetry-install
```

## Лицензия

MIT License - см. файл LICENSE для деталей.
