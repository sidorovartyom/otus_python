"""FastAPI приложение для инференса ML модели с JWT аутентификацией."""
import pickle
import logging
from datetime import timedelta
from pathlib import Path
from typing import Optional

import numpy as np
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse

from app.models import (
    IrisFeatures,
    PredictionResponse,
    HealthResponse,
    UserRegister,
    UserLogin,
    Token,
    UserResponse
)
from app.auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
    register_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаем приложение
app = FastAPI(
    title="ML Model Serving API with JWT Auth",
    description="REST API для предсказания классов ирисов с JWT аутентификацией и RBAC",
    version="2.0.0",
)

# Глобальные переменные для модели
model: Optional[object] = None
class_names: Optional[list] = None


@app.on_event("startup")
async def load_model():
    """Загружает модель при старте приложения."""
    global model, class_names

    try:
        model_path = Path("model.pkl")
        class_names_path = Path("class_names.pkl")

        if not model_path.exists():
            logger.error("Файл модели model.pkl не найден!")
            return

        with open(model_path, "rb") as f:
            model = pickle.load(f)
        logger.info("Модель успешно загружена")

        if class_names_path.exists():
            with open(class_names_path, "rb") as f:
                class_names = pickle.load(f)
            logger.info(f"Классы загружены: {class_names}")
        else:
            class_names = ["setosa", "versicolor", "virginica"]
            logger.warning("Файл с названиями классов не найден, используются значения по умолчанию")

    except Exception as e:
        logger.error(f"Ошибка при загрузке модели: {e}")


@app.get("/", response_model=dict)
async def root():
    """Корневой эндпоинт."""
    return {
        "message": "ML Model Serving API",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Проверка работоспособности сервиса."""
    return HealthResponse(
        status="healthy" if model is not None else "unhealthy",
        model_loaded=model is not None,
    )


# Эндпоинты аутентификации

@app.post("/register", response_model=UserResponse)
async def register(user: UserRegister):
    """
    Регистрация нового пользователя.

    Args:
        user: Данные пользователя (username, password, role)

    Returns:
        UserResponse: Информация о зарегистрированном пользователе
    """
    try:
        new_user = register_user(user.username, user.password, user.role)
        logger.info(f"Новый пользователь зарегистрирован: {user.username}")
        return UserResponse(**new_user)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Ошибка при регистрации: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/login", response_model=Token)
async def login(user: UserLogin):
    """
    Вход пользователя и получение JWT токена.

    Args:
        user: Логин и пароль

    Returns:
        Token: JWT токен для доступа к защищенным эндпоинтам
    """
    authenticated_user = authenticate_user(user.username, user.password)

    if not authenticated_user:
        raise HTTPException(
            status_code=401,
            detail="Неверное имя пользователя или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": authenticated_user["username"], "role": authenticated_user["role"]},
        expires_delta=access_token_expires
    )

    logger.info(f"Пользователь {user.username} успешно вошел")

    return Token(access_token=access_token, token_type="bearer")


@app.get("/me", response_model=UserResponse)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    """
    Получить информацию о текущем пользователе.

    Args:
        current_user: Текущий авторизованный пользователь

    Returns:
        UserResponse: Информация о пользователе
    """
    return UserResponse(username=current_user["username"], role=current_user["role"])


# Защищенные эндпоинты

@app.post("/predict", response_model=PredictionResponse)
async def predict(
    features: IrisFeatures,
    current_user: dict = Depends(get_current_user)
):
    """
    Выполняет предсказание класса ириса на основе входных признаков.

    Требует авторизации (JWT токен).

    Args:
        features: Признаки цветка (длина и ширина чашелистика и лепестка)
        current_user: Текущий авторизованный пользователь

    Returns:
        PredictionResponse: Предсказанный класс и вероятность
    """
    if model is None:
        logger.error("Модель не загружена")
        raise HTTPException(status_code=503, detail="Модель не загружена")

    logger.info(f"Запрос на предсказание от пользователя: {current_user['username']} ({current_user['role']})")

    try:
        # Преобразуем входные данные в массив numpy
        input_data = np.array(
            [
                [
                    features.sepal_length,
                    features.sepal_width,
                    features.petal_length,
                    features.petal_width,
                ]
            ]
        )

        # Делаем предсказание
        prediction = model.predict(input_data)[0]
        probabilities = model.predict_proba(input_data)[0]

        # Получаем название класса и вероятность
        predicted_class = class_names[prediction]
        probability = float(probabilities[prediction])

        logger.info(
            f"Предсказание: {predicted_class} (вероятность: {probability:.2f})"
        )

        return PredictionResponse(
            prediction=predicted_class, probability=probability
        )

    except Exception as e:
        logger.error(f"Ошибка при предсказании: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка при предсказании: {str(e)}")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Обработчик всех необработанных исключений."""
    logger.error(f"Необработанная ошибка: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Внутренняя ошибка сервера"},
    )
