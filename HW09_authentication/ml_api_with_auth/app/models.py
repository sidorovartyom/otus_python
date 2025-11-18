"""Pydantic модели для валидации запросов и ответов."""
from pydantic import BaseModel, Field


class IrisFeatures(BaseModel):
    """Входные признаки для классификации ириса."""

    sepal_length: float = Field(..., ge=0, description="Длина чашелистика (см)")
    sepal_width: float = Field(..., ge=0, description="Ширина чашелистика (см)")
    petal_length: float = Field(..., ge=0, description="Длина лепестка (см)")
    petal_width: float = Field(..., ge=0, description="Ширина лепестка (см)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "sepal_length": 5.1,
                    "sepal_width": 3.5,
                    "petal_length": 1.4,
                    "petal_width": 0.2,
                }
            ]
        }
    }


class PredictionResponse(BaseModel):
    """Ответ с предсказанием модели."""

    prediction: str = Field(..., description="Предсказанный класс")
    probability: float = Field(..., ge=0, le=1, description="Вероятность предсказания")

    model_config = {
        "json_schema_extra": {
            "examples": [{"prediction": "setosa", "probability": 0.95}]
        }
    }


class HealthResponse(BaseModel):
    """Ответ health check."""

    status: str = Field(..., description="Статус сервиса")
    model_loaded: bool = Field(..., description="Загружена ли модель")


# Модели для аутентификации

class UserRegister(BaseModel):
    """Модель для регистрации пользователя."""

    username: str = Field(..., min_length=3, max_length=50, description="Имя пользователя")
    password: str = Field(..., min_length=6, description="Пароль")
    role: str = Field(default="user", description="Роль пользователя (user/admin)")


class UserLogin(BaseModel):
    """Модель для логина пользователя."""

    username: str
    password: str


class Token(BaseModel):
    """Модель токена."""

    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Данные из токена."""

    username: str
    role: str


class UserResponse(BaseModel):
    """Ответ с данными пользователя."""

    username: str
    role: str
