# Руководство по тестированию

Это руководство объясняет, как запускать тесты для проекта Crypto Pairs API.

## Для новых разработчиков (без настроенного окружения)

### Минимальные требования
- Docker 20.10+
- Docker Compose 2.0+  
- Make
- 4GB RAM

### Быстрый старт

1. **Клонируйте репозиторий:**
```bash
git clone <repository-url>
cd cryptopair
```

2. **Запустите автоматическую настройку:**
```bash
make setup-test
```

Эта команда:
- ✅ Проверит наличие всех требований
- 🐳 Соберет Docker образы
- 🧪 Запустит все тесты
- 📋 Покажет доступные команды

**Готово!** Никаких дополнительных настроек не требуется.

## Типы тестов

### 1. Unit тесты
Тестируют отдельные компоненты в изоляции:
```bash
make test-unit
```

### 2. Integration тесты  
Тестируют взаимодействие компонентов:
```bash
make test-integration
```

### 3. Нагрузочные тесты
Тестируют производительность под нагрузкой:
```bash
# Простой нагрузочный тест
make test-load

# Стресс-тест  
make test-stress

# k6 тест (требует установки k6)
make k6-test

# Locust с веб-интерфейсом
make locust-test

# Python benchmark suite
make benchmark
```

## Способы запуска тестов

### 1. Docker (рекомендуется)
Изолированное окружение, не требует локальной установки Python:

```bash
# Все тесты в Docker
make test-docker

# CI/CD режим
make test-ci
```

### 2. В работающем приложении
Если приложение уже запущено (`make up`):

```bash
# Все тесты
make test

# С покрытием кода
make test-all
```

### 3. Локально (для разработки)
Требует Poetry и Python 3.11+:

```bash
# Установить зависимости
make install-deps

# Запустить тесты
poetry run pytest tests/ -v
```

## Структура тестов

```
tests/
├── unit/                    # Unit тесты
│   ├── application/        # Тесты use cases
│   ├── domain/            # Тесты бизнес-логики
│   └── infrastructure/    # Тесты внешних сервисов
├── integration/            # Integration тесты
├── load/                  # Нагрузочные тесты
├── conftest.py           # Общие фикстуры
└── pytest.ini            # Конфигурация pytest
```

## Покрытие кода

После запуска тестов с покрытием:
- **Терминал**: показывает краткий отчет  
- **HTML**: откройте `coverage/index.html`
- **XML**: файл `coverage.xml` для CI/CD

## Отладка тестов

### Запуск конкретного теста
```bash
# Конкретный файл
pytest tests/unit/domain/test_crypto_price.py -v

# По паттерну
pytest tests/ -k "cache" -v

# По маркеру
pytest tests/ -m "unit" -v
```

### Дебаг в контейнере
```bash
# Доступ к shell контейнера
make shell

# Внутри контейнера
pytest tests/unit/domain/test_crypto_price.py -v -s --pdb
```

## Устранение проблем

### Docker не найден
```bash
# Ubuntu/Debian
sudo apt-get update && sudo apt-get install docker.io docker-compose

# macOS
brew install docker docker-compose
```

### Порты заняты
```bash
# Остановить все сервисы
make down

# Очистить систему
make clean
```

### Недостаточно памяти
```bash
# Проверить использование
docker stats

# Увеличить лимиты Docker (macOS/Windows)
# Docker Desktop -> Settings -> Resources -> Memory
```

### Тесты падают из-за зависимостей
```bash
# Пересобрать образы
docker-compose -f docker-compose.test.yml build --no-cache

# Или полная очистка
make clean && make setup-test
```

## CI/CD интеграция

Для автоматических pipelines используйте:

```yaml
# GitHub Actions пример
- name: Run tests
  run: make test-ci
```

Команда `make test-ci`:
- Собирает свежие образы
- Запускает все тесты
- Генерирует XML отчеты
- Автоматически очищает ресурсы

## Производительность тестов

Типичное время выполнения:
- **Unit тесты**: ~5-10 сек
- **Integration тесты**: ~15-30 сек  
- **Полный набор**: ~1-2 мин
- **Нагрузочные тесты**: ~2-5 мин

## Лучшие практики

1. **Всегда запускайте тесты перед коммитом**
2. **Используйте Docker для изоляции**
3. **Поддерживайте покрытие > 80%**
4. **Пишите тесты для новых функций**
5. **Тестируйте не только успешные сценарии**

---

💡 **Совет**: Начните с `make setup-test` - это самый простой способ начать работу с проектом!