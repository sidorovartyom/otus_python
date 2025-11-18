# ML Model Serving API с JWT Аутентификацией

REST API для инференса ML модели классификации ирисов с JWT аутентификацией и RBAC на основе FastAPI.

## Описание

Расширение API из WH08 с добавлением:
- **JWT аутентификация** - защищенные эндпоинты требуют токен
- **RBAC** - разграничение прав доступа (роли: admin, user)
- **Регистрация пользователей** - создание новых учетных записей
- **Безопасное хранение паролей** - хеширование с bcrypt

Приложение предоставляет REST API для предсказания вида ириса (Setosa, Versicolor, Virginica) на основе четырех признаков:
- Длина чашелистика (sepal length)
- Ширина чашелистика (sepal width)
- Длина лепестка (petal length)
- Ширина лепестка (petal width)

## Структура проекта

```
ml_api_with_auth/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI приложение с аутентификацией
│   ├── models.py        # Pydantic модели (включая User, Token)
│   └── auth.py          # JWT и RBAC логика
├── tests/
│   ├── __init__.py
│   └── test_api.py      # Тесты
├── train_model.py       # Скрипт обучения модели
├── test_auth.py         # Скрипт тестирования аутентификации
├── requirements.txt     # Зависимости
├── model.pkl           # Обученная модель
├── class_names.pkl     # Названия классов
└── README.md
```

## Установка

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Модель уже обучена и находится в файлах `model.pkl` и `class_names.pkl`

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

### Публичные (без авторизации)

#### GET /
Корневой эндпоинт с информацией о сервисе.

#### GET /health
Проверка работоспособности сервиса и статуса загрузки модели.

**Ответ:**
```json
{
  "status": "healthy",
  "model_loaded": true
}
```

#### POST /register
Регистрация нового пользователя.

**Запрос:**
```json
{
  "username": "newuser",
  "password": "password123",
  "role": "user"
}
```

**Ответ:**
```json
{
  "username": "newuser",
  "role": "user"
}
```

#### POST /login
Вход и получение JWT токена.

**Запрос:**
```json
{
  "username": "newuser",
  "password": "password123"
}
```

**Ответ:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Защищенные (требуют JWT токен)

#### GET /me
Получить информацию о текущем пользователе.

**Headers:**
```
Authorization: Bearer <your_jwt_token>
```

**Ответ:**
```json
{
  "username": "newuser",
  "role": "user"
}
```

#### POST /predict
Выполняет предсказание класса ириса (требует авторизацию).

**Headers:**
```
Authorization: Bearer <your_jwt_token>
```

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
  "probability": 1.0
}
```

## Примеры использования

### Python

```python
import requests

BASE_URL = "http://127.0.0.1:8000"

# 1. Регистрация
response = requests.post(
    f"{BASE_URL}/register",
    json={"username": "testuser", "password": "test123", "role": "user"}
)
print(response.json())

# 2. Логин
response = requests.post(
    f"{BASE_URL}/login",
    json={"username": "testuser", "password": "test123"}
)
token = response.json()["access_token"]

# 3. Предсказание с токеном
headers = {"Authorization": f"Bearer {token}"}
response = requests.post(
    f"{BASE_URL}/predict",
    json={"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2},
    headers=headers
)
print(response.json())
```

### cURL

```bash
# Регистрация
curl -X POST http://127.0.0.1:8000/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "test123", "role": "user"}'

# Логин и сохранение токена
TOKEN=$(curl -X POST http://127.0.0.1:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "test123"}' \
  | jq -r '.access_token')

# Предсказание с токеном
curl -X POST http://127.0.0.1:8000/predict \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}'
```

## Тестирование

### Автоматическое тестирование аутентификации
```bash
python test_auth.py
```

Скрипт проверит:
- Доступ без токена (должен вернуть 401)
- Регистрацию нового пользователя
- Логин и получение токена
- Доступ к защищенным эндпоинтам с токеном

### Pytest
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
- `401 Unauthorized` - нет токена или токен невалидный
- `403 Forbidden` - недостаточно прав (RBAC)
- `422 Unprocessable Entity` - ошибка валидации входных данных
- `500 Internal Server Error` - ошибка при обработке запроса
- `503 Service Unavailable` - модель не загружена

## RBAC (Role-Based Access Control)

Система поддерживает роли:
- **user** - обычный пользователь, может делать предсказания
- **admin** - администратор, имеет полный доступ

Функция `require_role()` в `app/auth.py` позволяет ограничить доступ к эндпоинтам по ролям.

## Безопасность

- Пароли хешируются с помощью bcrypt
- JWT токены подписываются с помощью HS256
- Время жизни токена: 30 минут (настраивается в `app/auth.py`)
- В продакшене SECRET_KEY должен быть в переменных окружения

## Логирование

Приложение логирует:
- Загрузку модели при старте
- Регистрацию и вход пользователей
- Все предсказания с информацией о пользователе
- Ошибки при обработке запросов

## Отличия от WH08

- ✅ Добавлена JWT аутентификация
- ✅ Защищен эндпоинт `/predict` (требует токен)
- ✅ Добавлены эндпоинты `/register`, `/login`, `/me`
- ✅ Реализован RBAC с ролями user/admin
- ✅ Добавлено логирование запросов от пользователей
- ✅ Безопасное хранение паролей (bcrypt)
