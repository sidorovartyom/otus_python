"""Скрипт для обучения и сохранения ML модели."""
import pickle
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split


def train_and_save_model():
    """Обучает модель на датасете Iris и сохраняет её в файл."""
    # Загружаем датасет Iris
    iris = load_iris()
    X, y = iris.data, iris.target

    # Разделяем на train/test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Обучаем модель
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # Проверяем точность
    accuracy = model.score(X_test, y_test)
    print(f"Точность модели на тестовой выборке: {accuracy:.2f}")

    # Сохраняем модель
    with open("model.pkl", "wb") as f:
        pickle.dump(model, f)

    print("Модель сохранена в файл model.pkl")

    # Сохраняем названия классов для удобства
    class_names = iris.target_names.tolist()
    with open("class_names.pkl", "wb") as f:
        pickle.dump(class_names, f)

    print(f"Классы: {class_names}")


if __name__ == "__main__":
    train_and_save_model()
