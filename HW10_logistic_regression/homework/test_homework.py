# -*- coding: utf-8 -*-
"""Скрипт для проверки домашнего задания по логистической регрессии."""
import sys
import os

# Настройка кодировки для Windows
if sys.platform == 'win32':
    os.system('chcp 65001 >nul')
    sys.stdout.reconfigure(encoding='utf-8')

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

from dmia.classifiers import LogisticRegression
from dmia.gradient_check import grad_check_sparse

print("=" * 60)
print("ПРОВЕРКА ДОМАШНЕГО ЗАДАНИЯ: ЛОГИСТИЧЕСКАЯ РЕГРЕССИЯ")
print("=" * 60)

# 1. Загрузка данных
print("\n1. Загрузка данных...")
try:
    train_df = pd.read_csv('./data/train.csv')
    print(f"   [OK] Загружено {train_df.shape[0]} примеров")
    print(f"   [OK] Классы: {train_df.Prediction.value_counts().to_dict()}")
except Exception as e:
    print(f"   [ОШИБКА] Ошибка загрузки данных: {e}")
    sys.exit(1)

# 2. Подготовка данных
print("\n2. Подготовка данных (TF-IDF векторизация)...")
review_summaries = [l.lower() for l in train_df['Reviews_Summary'].values]
vectorizer = TfidfVectorizer(max_features=1000)
X = vectorizer.fit_transform(review_summaries)
y = train_df.Prediction.values
X_train, X_test, y_train, y_test = train_test_split(X, y, train_size=0.7, random_state=42)
print(f"   [OK] Train: {X_train.shape[0]} примеров, {X_train.shape[1]} признаков")
print(f"   [OK] Test: {X_test.shape[0]} примеров")

# 3. Проверка градиента
print("\n3. Gradient Check (проверка корректности градиента)...")
X_sample = X_train[:1000]
y_sample = y_train[:1000]
clf = LogisticRegression()
clf.w = np.random.randn(X_sample.shape[1] + 1) * 0.01

loss, grad = clf.loss(LogisticRegression.append_biases(X_sample), y_sample, 0.0)
f = lambda w: clf.loss(LogisticRegression.append_biases(X_sample), y_sample, 0.0)[0]

print("   Проверка 5 случайных элементов градиента:")
grad_check_sparse(f, clf.w, grad, 5)
print("   [OK] Gradient Check завершен (relative error < 1e-5 - хорошо)")

# 4. Обучение модели
print("\n4. Обучение логистической регрессии...")
clf = LogisticRegression()
clf.train(X_train, y_train,
          learning_rate=1.0,
          num_iters=500,
          batch_size=256,
          reg=1e-3,
          verbose=False)
print("   [OK] Обучение завершено")

# 5. Оценка качества
print("\n5. Оценка качества модели...")
train_pred = clf.predict(X_train)
test_pred = clf.predict(X_test)

train_acc = accuracy_score(y_train, train_pred)
test_acc = accuracy_score(y_test, test_pred)

print(f"   Train Accuracy: {train_acc:.3f}")
print(f"   Test Accuracy:  {test_acc:.3f}")

if test_acc > 0.75:
    print("   [OK] Качество хорошее (> 75%)")
else:
    print("   [ВНИМАНИЕ] Низкое качество, проверьте реализацию")

# 6. Сравнение со sklearn
print("\n6. Сравнение со sklearn.linear_model.SGDClassifier...")
from sklearn.linear_model import SGDClassifier

sklearn_clf = SGDClassifier(
    max_iter=500,
    random_state=42,
    loss="log_loss",
    penalty="l2",
    alpha=1e-3,
    eta0=1.0,
    learning_rate="constant"
)
sklearn_clf.fit(X_train, y_train)
sklearn_test_acc = accuracy_score(y_test, sklearn_clf.predict(X_test))

print(f"   Наша модель: {test_acc:.3f}")
print(f"   Sklearn:     {sklearn_test_acc:.3f}")
print(f"   Разница:     {abs(test_acc - sklearn_test_acc):.3f}")

if abs(test_acc - sklearn_test_acc) < 0.05:
    print("   [OK] Разница < 5%, реализация корректна!")
else:
    print("   [ВНИМАНИЕ] Большая разница, проверьте реализацию")

# 7. Анализ важных слов
print("\n7. Топ-5 слов для каждого класса...")
feature_names = vectorizer.get_feature_names_out()
pos_features = np.argsort(clf.w)[-6:-1]  # Последний элемент - bias
neg_features = np.argsort(clf.w)[:5]

print("   Позитивные отзывы (класс 1):")
for idx in pos_features:
    if idx < len(feature_names):
        print(f"      - {feature_names[idx]}")

print("   Негативные отзывы (класс 0):")
for idx in neg_features:
    if idx < len(feature_names):
        print(f"      - {feature_names[idx]}")

print("\n" + "=" * 60)
print("ПРОВЕРКА ЗАВЕРШЕНА!")
print("=" * 60)
