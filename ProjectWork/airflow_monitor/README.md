# 🔄 Airflow DAG Health Monitor

**Система мониторинга здоровья Airflow DAG'ов с ML-детекцией аномалий**

Проектная работа курса "Python Developer" OTUS

---

## 🎯 Возможности

- 📊 **Сбор метрик** из Airflow metadata DB (ежедневные снимки)
- 🏥 **Health Score** для DAG'ов (0-100) на основе успешности и стабильности
- 🤖 **ML-детекция аномалий** (Isolation Forest, Z-score)
- 📈 **Streamlit dashboard** с интерактивной визуализацией
- 📉 **Тренды и история** с гибкой агрегацией (7/14/30 дней)
- 🔔 **Telegram алерты** (класс готов, опциональная интеграция)
- 📡 **Prometheus метрики** для интеграции с мониторингом

## 🏗️ Архитектура

### Daily Snapshot Architecture

Система использует **ежедневную** архитектуру хранения метрик:
- **Один день = один snapshot** в базе данных
- Агрегация выполняется "на лету" при отображении
- Пользователь выбирает период отображения без пересбора данных

### Компоненты

```
┌─────────────────────────────────────────────┐
│         Streamlit Dashboard (app_ru.py)     │
│  - Главная страница (обзор)                 │
│  - Детали DAG (тренды, графики)             │
│  - Аномалии (детекция, фильтры)             │
└──────────────────┬──────────────────────────┘
                   ↓
┌─────────────────────────────────────────────┐
│            Core Logic (airflow_monitor/)    │
│  ┌─────────────────────────────────────┐    │
│  │ MetricsCollector                    │    │
│  │  - Читает Airflow DB                │    │
│  │  - Собирает ежедневные метрики      │    │
│  └─────────────────────────────────────┘    │
│  ┌─────────────────────────────────────┐    │
│  │ HealthScorer                        │    │
│  │  - Формула: 70% success + 30% stab  │    │
│  │  - Категории: Excellent → Critical  │    │
│  └─────────────────────────────────────┘    │
│  ┌─────────────────────────────────────┐    │
│  │ AnomalyDetector                     │    │
│  │  - Isolation Forest ML              │    │
│  │  - Z-score статистика               │    │
│  └─────────────────────────────────────┘    │
│  ┌─────────────────────────────────────┐    │
│  │ MetricsExporter                     │    │
│  │  - Prometheus метрики               │    │
│  └─────────────────────────────────────┘    │
└──────────────────┬──────────────────────────┘
                   ↓
┌─────────────────────────────────────────────┐
│         Data Layer (db/)                    │
│  ┌─────────────────┐  ┌─────────────────┐   │
│  │  Airflow DB     │  │  SQLite         │   │
│  │  (read-only)    │  │  (metrics)      │   │
│  │  - dag_run      │  │  - dag_snapshots│   │
│  │  - task_inst    │  │  - anomalies    │   │
│  └─────────────────┘  └─────────────────┘   │
└─────────────────────────────────────────────┘
```

## 📦 Установка и быстрый старт

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Настройка окружения

Скопируйте `.env.example` в `.env` и настройте подключение к Airflow DB:

```bash
cp .env.example .env
```

Пример `.env`:
```ini
# Airflow database connection (read-only)
AIRFLOW_DB_URL=postgresql://airflow:airflow@localhost:5432/airflow

# Or use SQLite for testing
# AIRFLOW_DB_URL=sqlite:///path/to/airflow.db

# Telegram bot (optional)
TELEGRAM_BOT_TOKEN=your_token_here
TELEGRAM_CHAT_ID=your_chat_id
```

### 3. Инициализация базы данных

```bash
python scripts/init_db.py
```

### 4. Генерация демо-данных

**Для демонстрации без реального Airflow:**

```bash
python scripts/seed_demo_data.py
```

Это создаст:
- 6 DAG с разными сценариями (здоровый, деградирующий, нестабильный, проваливающийся)
- 180 ежедневных снимков (30 дней × 6 DAG)
- 3-5 аномалий для демонстрации

### 5. Запуск dashboard

```bash
streamlit run airflow_monitor/dashboard/app_ru.py
```

Откройте в браузере: **http://localhost:8501**

## 🚀 Использование

### Dashboard

1. **Главная страница** - обзор всех DAG:
   - Средний Health Score по всем DAG
   - Количество нездоровых DAG
   - Таблица с рейтингом по здоровью
   - Выбор периода агрегации (7, 14, 30 дней)

2. **Детали DAG** - подробная информация:
   - Тренды health score, длительности, успешности
   - Графики за выбранный период
   - История аномалий для конкретного DAG

3. **Аномалии** - детекция проблем:
   - Список всех аномалий
   - Фильтры по DAG и статусу
   - Временная линия аномалий
   - Возможность отметить как устраненные

### Запуск с реальным Airflow

Если у вас есть реальный Airflow:

1. Настройте `AIRFLOW_DB_URL` в `.env`
2. В dashboard нажмите **"Запустить анализ"**
3. Выберите период сбора (7-90 дней)
4. Система соберет метрики из Airflow DB и рассчитает health scores

### API сервер (Prometheus метрики)

```bash
python -m airflow_monitor.api_server
```

Метрики доступны на: **http://localhost:9090/metrics**

Примеры метрик:
```
# Health scores
airflow_dag_health_score{dag_id="etl_daily_sales"} 95.0

# Anomaly counts
airflow_dag_anomalies_count{dag_id="data_warehouse_sync"} 2.0
```

## 🧪 Тестирование

Запуск unit-тестов:

```bash
pytest tests/ -v
```

Тесты покрывают:
- Health Score расчеты
- Детекцию аномалий (Isolation Forest)
- Категоризацию health tiers

## 📊 Метрики и формулы

### Health Score

```
Health Score = 0.7 × Success Score + 0.3 × Stability Score

где:
- Success Score = avg(success_rate) × 100 за последние 7 дней
- Stability Score = 100 - (std(success_rate) × 1000)
```

### Health Tiers

| Score    | Tier        | Описание                    |
|----------|-------------|-----------------------------|
| 90-100   | 🟢 Excellent | Отличное состояние          |
| 75-89    | 🟡 Good      | Хорошо, небольшие проблемы  |
| 60-74    | 🟠 Fair      | Удовлетворительно           |
| 45-59    | 🔴 Poor      | Проблемы требуют внимания   |
| 0-44     | ⚫ Critical  | Критическое состояние       |

### Детекция аномалий

Используются два метода:
1. **Isolation Forest** - ML-алгоритм для выявления выбросов
2. **Z-score** - статистический метод (|z| > 2.0)

## 📝 Структура проекта

```
airflow_monitor/
├── airflow_monitor/           # Основной пакет
│   ├── core/                  # Бизнес-логика
│   │   ├── models.py          # DAGMetrics, AnomalyResult
│   │   ├── metrics_collector.py   # Сбор из Airflow DB
│   │   ├── health_scorer.py   # Расчет Health Score
│   │   ├── anomaly_detector.py    # ML детекция
│   │   ├── metrics_exporter.py    # Prometheus метрики
│   │   └── alerter.py         # Telegram уведомления
│   ├── db/                    # База данных
│   │   ├── database.py        # SQLAlchemy модели
│   │   └── repository.py      # CRUD операции
│   ├── dashboard/             # Streamlit UI
│   │   ├── app_ru.py          # Главное приложение (русский)
│   │   └── pages/             # Дополнительные страницы
│   │       ├── 1_DAG_Details.py   # Детали DAG
│   │       └── 2_Anomalies.py     # Аномалии
│   ├── api_server.py          # Prometheus /metrics endpoint
│   └── config.py              # Настройки
├── scripts/                   # Утилиты
│   ├── init_db.py             # Инициализация БД
│   └── seed_demo_data.py      # Генератор демо-данных
├── tests/                     # Unit-тесты
│   ├── test_health_scorer.py
│   └── test_anomaly_detector.py
├── README.md                  # Эта документация
├── .env.example               # Пример настроек
├── requirements.txt           # Зависимости
├── Dockerfile                 # Docker образ
├── docker-compose.yml         # Docker compose
```

## 🎓 Демонстрируемые навыки

**Python Core:**
- ООП и чистая архитектура (SOLID принципы)
- Dataclasses для моделей данных
- Type hints для всего кода
- Модульность и переиспользуемость

**Работа с данными:**
- SQLAlchemy ORM (модели, миграции)
- Repository паттерн для абстракции БД
- Pandas для обработки данных
- NumPy для численных расчетов

**Machine Learning:**
- scikit-learn (Isolation Forest)
- Статистические методы (Z-score, rolling windows)
- Feature engineering для аномалий

**Web и визуализация:**
- Streamlit для dashboard
- Plotly для интерактивных графиков
- Multi-page приложения

**DevOps и мониторинг:**
- Prometheus метрики
- Docker (docker-compose.yml)
- Environment configuration (.env)

**Тестирование:**
- pytest для unit-тестов
- Фикстуры и параметризация
- Моки для изоляции тестов

**Документация:**
- Docstrings для всех функций
- Markdown документация
- README для быстрого старта

## 🔧 Технологии

- **Python 3.10+**
- **Streamlit** - Dashboard UI
- **SQLAlchemy** - ORM для работы с БД
- **scikit-learn** - Machine Learning
- **Plotly** - Визуализация графиков
- **Prometheus Client** - Метрики
- **pytest** - Тестирование

## 📄 Лицензия

MIT

---

**Автор:** Артем Сидоров
**Курс:** Python Developer OTUS
**Проект:** Проектная работа
**Дата:** Декабрь 2025
