# Анализатор логов nginx

Анализатор логов nginx для создания отчетов о производительности веб-приложений. Скрипт анализирует логи nginx, извлекает статистику по URL'ам и генерирует HTML-отчеты.

## Структура проекта

```
HW01_log_analyzer/
├── log_analyzer/           # Основной пакет
│   ├── __init__.py        # Инициализация пакета
│   ├── analyzer.py        # Основной класс LogAnalyzer
│   └── config.py          # Работа с конфигурацией
├── tests/                 # Тесты
│   ├── __init__.py
│   └── test_analyzer.py   # Тесты для LogAnalyzer
├── log/                   # Директория для лог-файлов
├── reports/               # Директория для отчетов
├── setup.py              # Конфигурация пакета
├── requirements.txt       # Зависимости
├── Makefile              # Команды для разработки
├── README.md             # Документация
├── .gitignore            # Исключения Git
├── config.json           # Конфигурация по умолчанию
├── Dockerfile            # Docker образ
├── docker-compose.yml    # Docker Compose конфигурация
└── .dockerignore         # Исключения для Docker
```

## Возможности

- Автоматический поиск последнего лог-файла в директории
- Поддержка сжатых (gzip) и обычных лог-файлов
- Парсинг логов nginx с извлечением URL и времени запроса
- Вычисление статистики: количество запросов, среднее время, медиана, максимум
- Генерация HTML-отчетов с сортировкой по времени обработки
- Структурированное логирование в JSON формате
- Конфигурируемые параметры через JSON файл
- Проверка на превышение порога ошибок парсинга
- Объектно-ориентированная архитектура с классом LogAnalyzer
- **Docker поддержка для контейнеризации**

## Установка

### Локальная установка

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd HW01_log_analyzer
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Для разработки установите пакет в режиме разработки:
```bash
pip install -e .
```

### Docker установка

1. Убедитесь, что у вас установлен Docker и Docker Compose

2. Соберите Docker образ:
```bash
docker-compose build
```

## Использование

### Локальный запуск

#### Базовое использование

```bash
python -m log_analyzer
```

#### С кастомной конфигурацией

```bash
python -m log_analyzer --config config.json
```

#### После установки пакета

```bash
# Установить пакет
pip install -e .

# Запустить как команду
log-analyzer --config config.json
```

### Docker запуск

#### Одноразовый запуск

```bash
# Собрать образ
docker-compose build

# Запустить приложение
docker-compose up log-analyzer
```

#### Запуск в фоновом режиме

```bash
docker-compose up -d log-analyzer
```

#### Периодический запуск (каждый час)

```bash
docker-compose up -d log-analyzer-cron
```

#### Просмотр логов

```bash
docker-compose logs -f log-analyzer
```

#### Остановка

```bash
docker-compose down
```

### Использование Makefile

#### Локальные команды

```bash
make install      # Установить зависимости
make test         # Запустить тесты
make run          # Запустить приложение
make clean        # Очистить временные файлы
```

#### Docker команды

```bash
make docker-build     # Собрать Docker образ
make docker-run       # Запустить в Docker
make docker-stop      # Остановить контейнеры
make docker-logs      # Показать логи
make docker-test      # Запустить тесты в Docker
make docker-clean     # Очистить Docker
```

### Пример конфигурационного файла (config.json)

```json
{
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log",
    "LOG_FILE": "analyzer.log",
    "ERROR_THRESHOLD": 0.1
}
```

## Разработка

### Запуск тестов

```bash
# Все тесты
make test

# Тесты с покрытием
make test-coverage

# Или напрямую
pytest tests/ -v

# Тесты в Docker
make docker-test
```

### Проверка кода

```bash
make check
```

### Очистка

```bash
make clean
```

### Полный цикл разработки

```bash
make all  # установка, тесты, запуск
```

## API

### LogAnalyzer

Основной класс для анализа логов.

```python
from log_analyzer import LogAnalyzer
from log_analyzer.config import load_config

# Загрузка конфигурации
config = load_config('config.json')

# Создание анализатора
analyzer = LogAnalyzer(config)

# Запуск анализа
result = analyzer.run()
```

### Методы

- `find_latest_log(log_dir)` - поиск последнего лог-файла
- `parse_log_line(line)` - парсинг одной строки лога
- `parse_log_file(log_file_path)` - парсинг всего файла
- `parse_log_generator(log_file_path)` - генератор для парсинга
- `calculate_statistics(url_times)` - вычисление статистики
- `render_report(stats, report_date)` - создание HTML-отчета
- `save_report(report_html, report_date)` - сохранение отчета
- `run()` - основной метод запуска

## Формат логов

Анализатор поддерживает формат логов nginx:

```
log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '  
                    '$request_time';
```

## Формат отчетов

Отчеты генерируются в HTML формате с таблицей статистики:

| URL | Количество запросов | % запросов | Время обработки | % времени | Среднее время | Максимальное время | Медиана |
|-----|-------------------|------------|----------------|-----------|---------------|-------------------|---------|
| /api/v2/banner/25019354 | 1000 | 0.5% | 390.0 | 0.1% | 0.39 | 1.5 | 0.35 |

## Логирование

Анализатор использует structlog для структурированного логирования в JSON формате:

```json
{
    "event": "Найден последний лог-файл",
    "file": "nginx-access-ui.log-20170630.gz",
    "date": "2017-06-30",
    "logger": "log_analyzer.analyzer",
    "level": "info",
    "timestamp": "2025-07-23T21:01:58.462456Z"
}
```

## Docker

### Образ

Docker образ основан на `python:3.10-slim` и включает:

- Все необходимые зависимости
- Безопасного пользователя `appuser`
- Монтирование директорий для логов и отчетов
- Поддержку конфигурационных файлов

### Сервисы

- `log-analyzer` - одноразовый запуск анализатора
- `log-analyzer-cron` - периодический запуск каждый час

### Volumes

- `./log:/app/log:ro` - директория с логами (только чтение)
- `./reports:/app/reports` - директория для отчетов
- `./config.json:/app/config.json:ro` - конфигурация (только чтение)

## Требования

- Python 3.8+
- structlog
- pytest (для тестирования)
- Docker (опционально)
- Docker Compose (опционально)

## Лицензия

MIT License
