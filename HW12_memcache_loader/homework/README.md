# Memcache Loader - Concurrent Version

Многопоточная версия загрузчика логов трекера мобильных приложений в кластер memcache.

## Домашнее задание OTUS HW12

**Цель**: Оптимизировать однопоточный скрипт, загружающий данные в memcache, используя многопоточную обработку.

## Описание

Скрипт парсит и загружает в memcache поминутную выгрузку логов трекера установленных приложений.

**Формат данных:**
- Ключ: `<тип_устройства>:<идентификатор>` (например, `idfa:e7e1a50c...`)
- Значение: Protobuf сообщение с координатами и списком приложений

## Оптимизации

### Оригинальная версия (однопоточная):
```
❌ Последовательная обработка всех строк
❌ Новое подключение к memcache для каждой записи
❌ Нет переиспользования соединений
❌ Медленная работа с большими файлами (500MB+)
```

### Оптимизированная версия (многопоточная):
```
✅ ThreadPoolExecutor для параллельной обработки
✅ Persistent connections (connection pool)
✅ Thread-safe статистика
✅ Настраиваемое количество воркеров
✅ Сохранение хронологического порядка файлов
```

### Архитектура

```
[Файл .tsv.gz]
      ↓
[Чтение построчно (главный поток)]
      ↓
[ThreadPoolExecutor (N воркеров)]
      ├─ Воркер 1: parse → serialize → memcache
      ├─ Воркер 2: parse → serialize → memcache
      ├─ Воркер 3: parse → serialize → memcache
      └─ ...
      ↓
[Persistent connections к memcache]
      ↓
[Memcache cluster: idfa, gaid, adid, dvid]
```

### Ключевые улучшения

1. **MemcacheConnectionPool**
   - Переиспользование соединений
   - Thread-safe доступ
   - Одно соединение на поток на тип устройства

2. **ThreadPoolExecutor**
   - Параллельная обработка строк
   - Автоматическое управление потоками
   - as_completed() для эффективной обработки

3. **Thread-safe Statistics**
   - Безопасные счетчики с locks
   - Статистика по обработанным/ошибочным записям

4. **Сохранение порядка файлов**
   - Файлы обрабатываются последовательно
   - Внутри файла - параллельно
   - Переименование после успешной обработки

## Установка

### Требования
- Python 3.6+
- protobuf
- python-memcached

### Установка зависимостей

```bash
pip install protobuf python-memcached
```

### Генерация protobuf (если нужно)

```bash
# Установка protoc
brew install protobuf  # macOS
# или
apt-get install protobuf-compiler  # Linux

# Генерация Python кода
protoc --python_out=. appsinstalled.proto
```

## Использование

### Базовый запуск (dry run)

```bash
python memc_load_concurrent.py --pattern=./sample.tsv.gz --dry
```

### Реальная загрузка в memcache

```bash
python memc_load_concurrent.py \
    --pattern=/data/appsinstalled/*.tsv.gz \
    --idfa=127.0.0.1:33013 \
    --gaid=127.0.0.1:33014 \
    --adid=127.0.0.1:33015 \
    --dvid=127.0.0.1:33016 \
    --workers=8
```

### Опции

- `--pattern` - паттерн для поиска файлов (glob)
- `--dry` - режим отладки (не записывает в memcache)
- `--workers` - количество воркеров (по умолчанию: 4)
- `--idfa` - адрес memcache для idfa устройств
- `--gaid` - адрес memcache для gaid устройств
- `--adid` - адрес memcache для adid устройств
- `--dvid` - адрес memcache для dvid устройств
- `--log` - файл для логов
- `--test` - запустить тест protobuf

### Примеры

**Тест protobuf:**
```bash
python memc_load_concurrent.py --test
```

**С логированием:**
```bash
python memc_load_concurrent.py \
    --pattern=./sample.tsv.gz \
    --log=memc_load.log \
    --workers=4
```

**Много воркеров для больших файлов:**
```bash
python memc_load_concurrent.py \
    --pattern=/data/*.tsv.gz \
    --workers=16
```

## Тестирование

### Запуск тестов

```bash
# Все тесты
python -m pytest test_memc_load.py -v

# С покрытием
python -m pytest test_memc_load.py --cov=memc_load_concurrent --cov-report=html

# Конкретный тест
python -m pytest test_memc_load.py::TestParseAppsInstalled -v
```

### Или через unittest

```bash
python test_memc_load.py
```

### Покрытие тестами

Тесты покрывают:
- ✅ Парсинг TSV строк
- ✅ Сериализация protobuf
- ✅ Connection pool
- ✅ Thread-safe статистику
- ✅ Обработку ошибок
- ✅ Переименование файлов

## Производительность

### Теоретическое сравнение

| Параметр | Оригинал | Оптимизация | Прирост |
|----------|----------|-------------|---------|
| Обработка строк | Последовательно | Параллельно (N потоков) | ~N раз |
| Memcache connections | Новое каждый раз | Persistent pool | ~10-20x |
| Обработка файла 500MB | ~300 сек | ~40 сек (8 воркеров) | ~7.5x |

### Рекомендуемые настройки

- **Малые файлы (<100MB)**: `--workers=4`
- **Средние файлы (100-500MB)**: `--workers=8`
- **Большие файлы (>500MB)**: `--workers=16`

**Примечание:** Оптимальное число воркеров зависит от:
- Количества CPU ядер
- Скорости сети до memcache
- Размера файлов

## Структура проекта

```
HW12_memcache_loader/
├── memc_load_concurrent.py   # Оптимизированная версия
├── memc_load_original.py     # Оригинальная версия
├── test_memc_load.py          # Тесты
├── appsinstalled.proto        # Protobuf схема
├── appsinstalled_pb2.py       # Сгенерированный protobuf код
├── sample.tsv                 # Тестовые данные
├── sample.tsv.gz              # Тестовые данные (gzip)
└── README.md                  # Этот файл
```

## Формат данных

### TSV файл (sample.tsv)
```
idfa	1rfw452y52g2gq4g	55.55	42.42	1423,43,567,3,7,23
gaid	6rfw452y52g2gq4g	55.55	42.42	6423,43,567,3,7,23
```

Поля:
1. `dev_type` - тип устройства (idfa, gaid, adid, dvid)
2. `dev_id` - идентификатор устройства
3. `lat` - широта
4. `lon` - долгота
5. `apps` - список ID приложений через запятую

### Protobuf схема
```protobuf
message UserApps {
    repeated uint32 apps = 1;
    optional double lat = 2;
    optional double lon = 3;
}
```

## Обработка ошибок

Скрипт обрабатывает:
- ❌ Невалидные строки (пропускает)
- ❌ Неверные координаты (пропускает)
- ❌ Несуществующие типы устройств (логирует ошибку)
- ❌ Проблемы с memcache (логирует, продолжает)

**Критерий успеха:** Error rate < 1%

## Логирование

```
[2024.11.19 10:30:15] I Memc loader started with options: ...
[2024.11.19 10:30:15] I Found 3 files to process
[2024.11.19 10:30:15] I Processing /data/20170929000000.tsv.gz
[2024.11.19 10:30:45] I Acceptable error rate (0.50%). Successful load
[2024.11.19 10:30:45] I File processed: 10000 records, 50 errors
```

## PEP8

Код проверен на соответствие PEP8:

```bash
flake8 memc_load_concurrent.py --max-line-length=120
```

## Требования к ДЗ

✅ Работающий код
✅ Конкурентная обработка через threading
✅ Тесты (pytest/unittest)
✅ Соответствие PEP8
✅ Документация с примерами
✅ Сохранение хронологического порядка файлов
✅ Persistent connections

## Возможные улучшения

- [ ] Multiprocessing для CPU-интенсивных операций
- [ ] Async/await версия (aiohttp + aiomemcache)
- [ ] Retry механизм для memcache
- [ ] Batch inserts (группировка записей)
- [ ] Metrics и мониторинг (Prometheus)
- [ ] Graceful shutdown

## Автор

Создано для OTUS HW12 - Multithreading

## Лицензия

Образовательный проект для курса OTUS Python
