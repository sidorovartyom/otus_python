# ML Model Serving API

REST API для инференса ML модели классификации ирисов на основе FastAPI.

## Описание

Приложение предоставляет REST API для предсказания вида ириса (Setosa, Versicolor, Virginica) на основе четырех признаков:
- Длина чашелистика (sepal length)
- Ширина чашелистика (sepal width)
- Длина лепестка (petal length)
- Ширина лепестка (petal width)

## Структура проекта

```
WH08_ml_model_serving/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI приложение
│   └── models.py        # Pydantic модели
├── tests/
│   ├── __init__.py
│   └── test_api.py      # Тесты
├── train_model.py       # Скрипт обучения модели
├── requirements.txt     # Зависимости
├── model.pkl           # Сохраненная модель (создается после обучения)
├── class_names.pkl     # Названия классов (создается после обучения)
└── README.md
```

## Установка

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Обучите и сохраните модель:
```bash
python train_model.py
```

Это создаст файлы `model.pkl` и `class_names.pkl`.

## Запуск приложения

Запустите сервер с помощью uvicorn:

```bash
uvicorn app.main:app --reload
```

Сервер будет доступен по адресу: http://127.0.0.1:8000

## Документация API

После запуска сервера автоматическая документация доступна по адресам:
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## Эндпоинты

### GET /
Корневой эндпоинт с информацией о сервисе.

### GET /health
Проверка работоспособности сервиса и статуса загрузки модели.

**Пример ответа:**
```json
{
  "status": "healthy",
  "model_loaded": true
}
```

### POST /predict
Выполняет предсказание класса ириса.

**Запрос:**
```json
{
  "sepal_length": 5.1,
  "sepal_width": 3.5,
  "petal_length": 1.4,
  "petal_width": 0.2
}
```

**Ответ:**
```json
{
  "prediction": "setosa",
  "probability": 0.95
}
```

## Примеры использования

### cURL

```bash
# Health check
curl http://127.0.0.1:8000/health

# Предсказание
curl -X POST http://127.0.0.1:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}'
```

### Python

```python
import requests

# Health check
response = requests.get("http://127.0.0.1:8000/health")
print(response.json())

# Предсказание
data = {
    "sepal_length": 5.1,
    "sepal_width": 3.5,
    "petal_length": 1.4,
    "petal_width": 0.2
}
response = requests.post("http://127.0.0.1:8000/predict", json=data)
print(response.json())
```

## Запуск тестов

Запустите тесты с помощью pytest:

```bash
pytest tests/ -v
```

## Валидация данных

API автоматически валидирует входные данные с помощью Pydantic:
- Все поля обязательны
- Все значения должны быть числами >= 0
- При некорректных данных возвращается 422 Unprocessable Entity

## Обработка ошибок

- `200 OK` - успешное предсказание
- `422 Unprocessable Entity` - ошибка валидации входных данных
- `500 Internal Server Error` - ошибка при обработке запроса
- `503 Service Unavailable` - модель не загружена

## Логирование

Приложение логирует:
- Загрузку модели при старте
- Все предсказания с результатами
- Ошибки при обработке запросов
