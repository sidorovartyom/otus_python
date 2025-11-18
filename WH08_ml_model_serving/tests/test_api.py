"""Тесты для FastAPI приложения."""
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root():
    """Тест корневого эндпоинта."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "docs" in data
    assert "health" in data


def test_health_check():
    """Тест health check эндпоинта."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "model_loaded" in data
    assert data["status"] in ["healthy", "unhealthy"]


def test_predict_valid_input():
    """Тест предсказания с корректными данными."""
    # Пример setosa
    payload = {
        "sepal_length": 5.1,
        "sepal_width": 3.5,
        "petal_length": 1.4,
        "petal_width": 0.2,
    }
    response = client.post("/predict", json=payload)

    # Если модель не загружена, получим 503
    if response.status_code == 503:
        pytest.skip("Модель не загружена")

    assert response.status_code == 200
    data = response.json()
    assert "prediction" in data
    assert "probability" in data
    assert data["prediction"] in ["setosa", "versicolor", "virginica"]
    assert 0 <= data["probability"] <= 1


def test_predict_invalid_input_negative_values():
    """Тест предсказания с некорректными данными (отрицательные значения)."""
    payload = {
        "sepal_length": -1.0,
        "sepal_width": 3.5,
        "petal_length": 1.4,
        "petal_width": 0.2,
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 422  # Validation error


def test_predict_missing_field():
    """Тест предсказания с отсутствующим полем."""
    payload = {
        "sepal_length": 5.1,
        "sepal_width": 3.5,
        "petal_length": 1.4,
        # petal_width отсутствует
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 422  # Validation error


def test_predict_wrong_type():
    """Тест предсказания с неправильным типом данных."""
    payload = {
        "sepal_length": "not_a_number",
        "sepal_width": 3.5,
        "petal_length": 1.4,
        "petal_width": 0.2,
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 422  # Validation error


def test_predict_all_classes():
    """Тест предсказания для всех трех классов."""
    test_cases = [
        # Setosa
        {
            "sepal_length": 5.1,
            "sepal_width": 3.5,
            "petal_length": 1.4,
            "petal_width": 0.2,
        },
        # Versicolor
        {
            "sepal_length": 5.9,
            "sepal_width": 3.0,
            "petal_length": 4.2,
            "petal_width": 1.5,
        },
        # Virginica
        {
            "sepal_length": 6.3,
            "sepal_width": 2.9,
            "petal_length": 5.6,
            "petal_width": 1.8,
        },
    ]

    for payload in test_cases:
        response = client.post("/predict", json=payload)

        # Если модель не загружена, пропускаем тест
        if response.status_code == 503:
            pytest.skip("Модель не загружена")

        assert response.status_code == 200
        data = response.json()
        assert "prediction" in data
        assert "probability" in data
