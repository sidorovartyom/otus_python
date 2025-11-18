#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
import hashlib
import json
from datetime import datetime
from unittest.mock import Mock, patch

from scoring import get_score, get_interests
from store import MockStore


class TestGetScore:
    """Тесты для функции get_score"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.store = MockStore()
    
    def test_get_score_empty_params(self):
        """Тест с пустыми параметрами"""
        score = get_score(self.store)
        assert score == 0.0
    
    def test_get_score_with_phone_only(self):
        """Тест только с телефоном"""
        score = get_score(self.store, phone="71234567890")
        assert score == 1.5
    
    def test_get_score_with_email_only(self):
        """Тест только с email"""
        score = get_score(self.store, email="test@example.com")
        assert score == 1.5
    
    def test_get_score_with_birthday_and_gender(self):
        """Тест с датой рождения и полом"""
        birthday = datetime(1990, 1, 1)
        score = get_score(self.store, birthday=birthday, gender=1)
        assert score == 1.5
    
    def test_get_score_with_first_name_and_last_name(self):
        """Тест с именем и фамилией"""
        score = get_score(self.store, first_name="John", last_name="Doe")
        assert score == 0.5
    
    def test_get_score_with_all_params(self):
        """Тест со всеми параметрами"""
        birthday = datetime(1990, 1, 1)
        score = get_score(
            self.store,
            phone="71234567890",
            email="test@example.com",
            birthday=birthday,
            gender=1,
            first_name="John",
            last_name="Doe"
        )
        assert score == 5.0
    
    def test_get_score_with_cache_hit(self):
        """Тест с попаданием в кеш"""
        # Подготавливаем кеш
        key_parts = ["John", "Doe", "71234567890", "19900101"]
        key = "uid:" + hashlib.md5("".join(key_parts).encode('utf-8')).hexdigest()
        self.store.cache_set(key, "3.5", 3600)
        
        # Получаем скор - должен вернуться из кеша
        score = get_score(
            self.store,
            first_name="John",
            last_name="Doe",
            phone="71234567890",
            birthday=datetime(1990, 1, 1)
        )
        assert score == 3.5
    
    def test_get_score_with_cache_miss(self):
        """Тест с промахом кеша"""
        # Получаем скор без предварительной записи в кеш
        score = get_score(
            self.store,
            first_name="John",
            last_name="Doe",
            phone="71234567890"
        )
        assert score == 2.0
        
        # Проверяем, что значение записалось в кеш
        key_parts = ["John", "Doe", "71234567890", ""]
        key = "uid:" + hashlib.md5("".join(key_parts).encode('utf-8')).hexdigest()
        cached_value = self.store.cache_get(key)
        assert cached_value == "2.0"
    
    def test_get_score_key_generation(self):
        """Тест генерации ключа для кеша"""
        birthday = datetime(1990, 1, 1)
        
        # Вызываем функцию
        get_score(
            self.store,
            first_name="John",
            last_name="Doe",
            phone="71234567890",
            birthday=birthday
        )
        
        # Проверяем, что ключ сгенерирован правильно
        key_parts = ["John", "Doe", "71234567890", "19900101"]
        expected_key = "uid:" + hashlib.md5("".join(key_parts).encode('utf-8')).hexdigest()
        
        # Проверяем, что в кеше есть значение с правильным ключом
        cached_value = self.store.cache_get(expected_key)
        assert cached_value is not None
    
    @pytest.mark.parametrize("phone,email,birthday,gender,first_name,last_name,expected_score", [
        ("71234567890", None, None, None, None, None, 1.5),
        (None, "test@example.com", None, None, None, None, 1.5),
        (None, None, datetime(1990, 1, 1), 1, None, None, 1.5),
        (None, None, None, None, "John", "Doe", 0.5),
        ("71234567890", "test@example.com", None, None, None, None, 3.0),
        ("71234567890", "test@example.com", datetime(1990, 1, 1), 1, "John", "Doe", 5.0),
    ])
    def test_get_score_combinations(self, phone, email, birthday, gender, first_name, last_name, expected_score):
        """Параметризованный тест различных комбинаций параметров"""
        score = get_score(
            self.store,
            phone=phone,
            email=email,
            birthday=birthday,
            gender=gender,
            first_name=first_name,
            last_name=last_name
        )
        assert score == expected_score
    
    def test_get_score_with_store_failure(self):
        """Тест работы при недоступности хранилища"""
        # Настраиваем store для симуляции ошибок
        self.store.set_should_fail(True)
        
        # Функция должна работать даже при ошибках хранилища
        score = get_score(
            self.store,
            phone="71234567890",
            email="test@example.com"
        )
        assert score == 3.0


class TestGetInterests:
    """Тесты для функции get_interests"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.store = MockStore()
    
    def test_get_interests_existing(self):
        """Тест получения интересов существующего клиента"""
        # Подготавливаем данные в хранилище
        interests = ["books", "music", "sports"]
        self.store._storage["i:123"] = json.dumps(interests)
        
        # Получаем интересы
        result = get_interests(self.store, "123")
        assert result == interests
    
    def test_get_interests_not_found(self):
        """Тест получения интересов несуществующего клиента"""
        result = get_interests(self.store, "999")
        assert result == []
    
    def test_get_interests_invalid_json(self):
        """Тест с некорректными данными в хранилище"""
        # Подготавливаем некорректные данные
        self.store._storage["i:123"] = "invalid json"
        
        # Должно вернуться пустой список
        result = get_interests(self.store, "123")
        assert result == []
    
    def test_get_interests_empty_string(self):
        """Тест с пустой строкой в хранилище"""
        self.store._storage["i:123"] = ""
        
        result = get_interests(self.store, "123")
        assert result == []
    
    def test_get_interests_with_store_failure(self):
        """Тест работы при недоступности хранилища"""
        # Настраиваем store для симуляции ошибок
        self.store.set_should_fail(True)
        
        # При ошибках хранилища должно вернуться пустой список
        result = get_interests(self.store, "123")
        assert result == []
    
    @pytest.mark.parametrize("cid,stored_data,expected_result", [
        ("123", '["books", "music"]', ["books", "music"]),
        ("456", '[]', []),
        ("789", None, []),
        ("999", "", []),
        ("111", "invalid json", []),
    ])
    def test_get_interests_various_data(self, cid, stored_data, expected_result):
        """Параметризованный тест различных типов данных"""
        if stored_data is not None:
            self.store._storage[f"i:{cid}"] = stored_data
        
        result = get_interests(self.store, cid)
        assert result == expected_result


class TestScoringIntegration:
    """Интеграционные тесты для scoring модуля"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.store = MockStore()
    
    def test_score_and_interests_workflow(self):
        """Тест полного цикла работы с скорингом и интересами"""
        # 1. Вычисляем скор
        score = get_score(
            self.store,
            phone="71234567890",
            email="test@example.com",
            first_name="John",
            last_name="Doe"
        )
        assert score == 3.5
        
        # 2. Получаем интересы
        interests = get_interests(self.store, "123")
        assert interests == []
        
        # 3. Сохраняем интересы
        test_interests = ["books", "music"]
        self.store._storage["i:123"] = json.dumps(test_interests)
        
        # 4. Получаем интересы снова
        interests = get_interests(self.store, "123")
        assert interests == test_interests
    
    def test_cache_and_storage_separation(self):
        """Тест разделения кеша и хранилища"""
        # Проверяем, что кеш и хранилище работают независимо
        self.store.cache_set("test_key", "cache_value", 3600)
        self.store._storage["test_key"] = "storage_value"
        
        assert self.store.cache_get("test_key") == "cache_value"
        assert self.store.get("test_key") == "storage_value" 