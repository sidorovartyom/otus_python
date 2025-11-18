"""FastAPI приложение для инференса ML модели."""
import pickle
import logging
from pathlib import Path
from typing import Optional

import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from app.models import IrisFeatures, PredictionResponse, HealthResponse

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаем приложение
app = FastAPI(
    title="ML Model Serving API",
    description="REST API для предсказания классов ирисов",
    version="1.0.0",
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


@app.post("/predict", response_model=PredictionResponse)
async def predict(features: IrisFeatures):
    """
    Выполняет предсказание класса ириса на основе входных признаков.

    Args:
        features: Признаки цветка (длина и ширина чашелистика и лепестка)

    Returns:
        PredictionResponse: Предсказанный класс и вероятность
    """
    if model is None:
        logger.error("Модель не загружена")
        raise HTTPException(status_code=503, detail="Модель не загружена")

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
