# Django Polls Application

Production-ready Django приложение для опросов, реализующее полный Django Tutorial (Parts 1-5) и оформленное согласно лучшим практикам и принципам 12-factor app.

## Возможности

### Функционал приложения (Django Tutorial Parts 1-5)
- ✅ **Список опросов** - просмотр доступных опросов
- ✅ **Детали опроса** - просмотр вопроса и вариантов ответа
- ✅ **Голосование** - возможность проголосовать за выбранный вариант
- ✅ **Результаты** - просмотр результатов голосования
- ✅ **Django Admin** - полнофункциональная админ-панель для управления опросами
- ✅ **Модели** - Question и Choice с связями
- ✅ **Тесты** - 10 тестов с 100% покрытием ключевого кода

### Production-ready настройки
- ✅ Конфигурация через переменные окружения (12-factor app)
- ✅ Логирование в stdout
- ✅ Static files serving через Whitenoise
- ✅ Docker поддержка
- ✅ Gunicorn WSGI server
- ✅ Комплексное тестирование

## Технологии

- Python 3.10
- Django 5.1
- Gunicorn (WSGI server)
- Whitenoise (static files)
- SQLite (database)
- Docker

## Структура проекта

```
WH07_django_tutorial/
├── manage.py
├── mysite/              # Основной модуль проекта
│   ├── settings.py      # Настройки с переменными окружения
│   ├── urls.py
│   └── wsgi.py
├── polls/               # Приложение для опросов
│   ├── models.py
│   ├── views.py
│   └── urls.py
├── requirements.txt     # Зависимости Python
├── Dockerfile          # Docker конфигурация
├── .env.example        # Пример переменных окружения
└── README.md
```

## Установка и запуск

### Локальная разработка

1. Клонируйте репозиторий и перейдите в директорию проекта:
```bash
cd WH07_django_tutorial
```

2. Создайте виртуальное окружение и активируйте его:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Создайте файл `.env` на основе `.env.example`:
```bash
cp .env.example .env
```

5. Отредактируйте `.env` и установите нужные значения:
```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

6. Примените миграции:
```bash
python manage.py migrate
```

7. Создайте суперпользователя (опционально):
```bash
python manage.py createsuperuser
```

8. Запустите сервер разработки:
```bash
python manage.py runserver
```

Приложение будет доступно по адресу: http://127.0.0.1:8000/

### Production деплой с Docker

1. Создайте файл `.env` для production:
```env
SECRET_KEY=your-production-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
LOG_LEVEL=WARNING
```

2. Соберите Docker образ:
```bash
docker build -t django-polls .
```

3. Запустите контейнер:
```bash
docker run -d \
  -p 8000:8000 \
  --env-file .env \
  --name django-polls \
  django-polls
```

4. Примените миграции (первый запуск):
```bash
docker exec django-polls python manage.py migrate
```

5. Создайте суперпользователя (первый запуск):
```bash
docker exec -it django-polls python manage.py createsuperuser
```

## Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `SECRET_KEY` | Django secret key | (обязательно для production) |
| `DEBUG` | Режим отладки | `True` |
| `ALLOWED_HOSTS` | Разрешенные хосты | `localhost,127.0.0.1` |
| `LOG_LEVEL` | Уровень логирования | `INFO` |
| `DJANGO_LOG_LEVEL` | Уровень логирования Django | `INFO` |

## Принципы 12-factor app

Проект реализует следующие принципы:

1. **Codebase** - единый репозиторий для разных окружений
2. **Dependencies** - явное объявление зависимостей в `requirements.txt`
3. **Config** - конфигурация через переменные окружения
4. **Logs** - логи выводятся в stdout
5. **Dev/prod parity** - одинаковое поведение в разных окружениях
6. **Processes** - stateless приложение, готовое к масштабированию

## Тестирование

Запуск тестов:
```bash
pytest
```

С покрытием:
```bash
pytest --cov=polls --cov-report=html
```

## Линтинг и форматирование

Проверка кода:
```bash
flake8 .
```

Форматирование:
```bash
black .
```

## API Endpoints

### Публичные страницы
- `/polls/` - Список всех опросов
- `/polls/<question_id>/` - Детали конкретного опроса с формой голосования
- `/polls/<question_id>/results/` - Результаты голосования
- `/polls/<question_id>/vote/` - Обработка голосования (POST)

### Административная панель
- `/admin/` - Админ-панель Django для управления опросами

## Использование

### Создание опроса через админку

1. Создайте суперпользователя:
```bash
python manage.py createsuperuser
```

2. Запустите сервер и перейдите в админку:
```bash
python manage.py runserver
# Откройте http://127.0.0.1:8000/admin/
```

3. Создайте вопрос (Question) и варианты ответа (Choices)

4. Перейдите на `/polls/` чтобы увидеть список опросов

## Лицензия

Учебный проект для курса OTUS Python

## Автор

[Ваше имя]
