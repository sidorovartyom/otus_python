# Hacker News Async Crawler

Асинхронный краулер для новостного сайта [Hacker News](https://news.ycombinator.com), реализованный с использованием `asyncio` и `aiohttp`.

## Описание

Краулер собирает топовые новости с Hacker News, извлекает комментарии и автоматически находит все ссылки в комментариях. Все данные сохраняются в SQLite базу данных для последующего анализа.

### Возможности

- ✅ Асинхронная загрузка новостей через официальный Hacker News API
- ✅ Параллельная обработка множественных новостей и комментариев
- ✅ Рекурсивный обход всех комментариев (включая вложенные)
- ✅ Автоматическое извлечение URL из текста комментариев
- ✅ Сохранение данных в SQLite с индексами для быстрого поиска
- ✅ Периодический запуск краулера (каждые N секунд)
- ✅ Защита от дублирования - уже обработанные новости пропускаются
- ✅ Логирование и статистика

## Архитектура

### Структура проекта

```
homework/
├── crawler.py       # Основной модуль краулера
├── models.py        # Модели данных (Story, Comment)
├── storage.py       # Работа с SQLite БД
├── test_crawler.py  # Тесты
├── requirements.txt # Зависимости
└── README.md        # Документация
```

### Компоненты

#### 1. Models (`models.py`)

Определяет структуры данных:

- **Story**: новость с полями `id`, `title`, `url`, `by`, `time`, `score`, `descendants`, `kids`
- **Comment**: комментарий с полями `id`, `by`, `time`, `text`, `parent`, `kids`

#### 2. Storage (`storage.py`)

Асинхронное хранилище на основе `aiosqlite`:

- **Таблица stories**: хранит новости
- **Таблица comments**: хранит комментарии
- **Таблица comment_links**: хранит извлеченные ссылки из комментариев
- Автоматическое извлечение URL из текста с помощью регулярных выражений
- Индексы для быстрого поиска

#### 3. Crawler (`crawler.py`)

Основной класс `HackerNewsCrawler`:

- Использует `aiohttp` для асинхронных HTTP запросов
- `asyncio.gather()` для параллельной обработки
- Context manager для управления сессией
- Обработка ошибок и таймаутов

### Принцип работы

1. **Получение топ-новостей**: запрос к `/v0/topstories.json`
2. **Параллельная загрузка**: создание задач для каждой новости
3. **Обработка новости**:
   - Загрузка деталей через `/v0/item/{id}.json`
   - Сохранение в БД
   - Загрузка всех комментариев (рекурсивно)
4. **Обработка комментария**:
   - Извлечение текста
   - Поиск URL с помощью regex
   - Сохранение комментария и ссылок

## Установка

1. Клонируйте репозиторий:
```bash
cd HW13_crawler/homework
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

## Использование

### Однократный запуск

Обработать 30 топовых новостей (по умолчанию):

```bash
python crawler.py
```

### Настройка параметров

```bash
python crawler.py --max-stories 50 --max-comments 200
```

- `--max-stories N`: максимальное количество новостей (по умолчанию: 30)
- `--max-comments N`: максимальное количество комментариев на новость (по умолчанию: 100)
- `--db PATH`: путь к БД SQLite (по умолчанию: `hackernews.db`)

### Периодический запуск

Запускать краулер каждые 300 секунд (5 минут):

```bash
python crawler.py --interval 300
```

### Примеры команд

```bash
# Обработать топ-10 новостей с максимум 50 комментариями
python crawler.py --max-stories 10 --max-comments 50

# Периодический запуск каждые 10 минут
python crawler.py --interval 600 --max-stories 30

# Использовать другую БД
python crawler.py --db /path/to/my_hn_data.db
```

## API Hacker News

Краулер использует официальный Firebase API:

- **Топ новостей**: `https://hacker-news.firebaseio.com/v0/topstories.json`
- **Детали item**: `https://hacker-news.firebaseio.com/v0/item/{id}.json`

Подробнее: [Hacker News API Documentation](https://github.com/HackerNews/API)

## База данных

### Схема

**stories**:
```sql
CREATE TABLE stories (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    url TEXT,
    by TEXT NOT NULL,
    time INTEGER NOT NULL,
    score INTEGER NOT NULL,
    descendants INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**comments**:
```sql
CREATE TABLE comments (
    id INTEGER PRIMARY KEY,
    story_id INTEGER NOT NULL,
    by TEXT NOT NULL,
    time INTEGER NOT NULL,
    text TEXT NOT NULL,
    parent INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (story_id) REFERENCES stories(id)
);
```

**comment_links**:
```sql
CREATE TABLE comment_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    comment_id INTEGER NOT NULL,
    story_id INTEGER NOT NULL,
    url TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (comment_id) REFERENCES comments(id),
    FOREIGN KEY (story_id) REFERENCES stories(id)
);
```

### Запросы к БД

Примеры полезных SQL запросов:

```sql
-- Топ-10 новостей по score
SELECT title, score, by FROM stories ORDER BY score DESC LIMIT 10;

-- Количество комментариев по новости
SELECT story_id, COUNT(*) as comments_count
FROM comments
GROUP BY story_id
ORDER BY comments_count DESC;

-- Все извлеченные ссылки
SELECT s.title, c.by, cl.url
FROM comment_links cl
JOIN comments c ON cl.comment_id = c.id
JOIN stories s ON cl.story_id = s.id;

-- Статистика по авторам
SELECT by, COUNT(*) as comment_count
FROM comments
GROUP BY by
ORDER BY comment_count DESC
LIMIT 20;
```

## Тестирование

Запуск тестов:

```bash
pytest test_crawler.py -v
```

Тесты покрывают:
- Создание моделей данных
- Работу с БД (сохранение, извлечение)
- Извлечение ссылок из текста
- Проверку существования новостей
- Контекстный менеджер краулера

## Производительность

### Асинхронная архитектура

Использование `asyncio` и `aiohttp` обеспечивает:

- **Параллельная обработка**: множественные новости загружаются одновременно
- **Неблокирующий I/O**: пока одна новость загружается, обрабатываются другие
- **Масштабируемость**: легко увеличить `max_stories` и `max_comments`

### Примерная производительность

- 30 новостей с ~50 комментариями каждая: **~15-30 секунд**
- 100 новостей: **~1-2 минуты**

(Зависит от скорости сети и текущей нагрузки на Hacker News API)

## Логирование

Краулер выводит подробные логи:

```
[2025-01-20 10:15:30] INFO Starting Hacker News crawl...
[2025-01-20 10:15:31] INFO Fetched 500 top story IDs
[2025-01-20 10:15:35] INFO Processing story 42167890: 'New breakthrough in quantum computing...'
[2025-01-20 10:15:40] INFO Story 42167890: saved 127 comments
[2025-01-20 10:16:00] INFO Crawl completed: 28/30 new stories processed
[2025-01-20 10:16:00] INFO Database stats: 128 stories, 3456 comments, 892 links
```

## Ограничения

- **Rate limiting**: Hacker News API не имеет жестких ограничений, но рекомендуется вежливое использование
- **Таймауты**: запросы с таймаутом 10 секунд, некоторые могут не загрузиться
- **Вложенность комментариев**: глубокая вложенность может увеличить время обработки

## Возможные улучшения

- [ ] Добавить `asyncio.Semaphore` для контроля количества одновременных запросов
- [ ] Реализовать retry механизм для failed requests
- [ ] Добавить кэширование результатов
- [ ] Экспорт данных в CSV/JSON
- [ ] Web интерфейс для просмотра данных
- [ ] Sentiment analysis комментариев
- [ ] Уведомления о новых трендовых новостях

## Зависимости

- `aiohttp>=3.9.0` - асинхронные HTTP запросы
- `aiosqlite>=0.19.0` - асинхронная работа с SQLite
- `pytest>=7.0.0` - тестирование
- `pytest-asyncio>=0.21.0` - поддержка асинхронных тестов

## Автор

Домашнее задание №13 для курса OTUS Python

## Лицензия

MIT
