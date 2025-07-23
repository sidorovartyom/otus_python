#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
import hashlib
import datetime
import json
from unittest.mock import Mock, patch

from api import (
    method_handler, check_auth, MethodRequest, OnlineScoreRequest, 
    ClientsInterestsRequest, CharField, EmailField, PhoneField, 
    DateField, BirthDayField, GenderField, ClientIDsField,
    ArgumentsField, OK, BAD_REQUEST, FORBIDDEN, NOT_FOUND, 
    INVALID_REQUEST, INTERNAL_ERROR, ADMIN_LOGIN, ADMIN_SALT, SALT
)
from store import MockStore


def cases(case_list):
    """Декоратор для параметризованных тестов"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            for i, case in enumerate(case_list):
                try:
                    func(*args, case, i)
                except Exception as e:
                    raise Exception(f"Case {i} failed: {case} - {str(e)}")
        return wrapper
    return decorator


class TestMethodHandler:
    """Тесты для method_handler"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.context = {}
        self.store = MockStore()
    
    def test_method_handler_empty_request(self):
        """Тест пустого запроса"""
        response, code = method_handler({"body": {}}, self.context, self.store)
        assert code == INVALID_REQUEST
        assert "Field is required" in response
    
    def test_method_handler_invalid_method(self):
        """Тест несуществующего метода"""
        # Создаем валидный токен для авторизации
        digest = hashlib.sha512(("test_account" + "test_login" + "Otus").encode('utf-8')).hexdigest()
        
        request = {
            "account": "test_account",
            "login": "test_login",
            "token": digest,
            "arguments": {},
            "method": "unknown_method"
        }
        
        response, code = method_handler({"body": request}, self.context, self.store)
        assert code == NOT_FOUND
        assert response == "Method not found"
    
    @cases([
        {
            "account": "horns&hoofs",
            "login": "h&f", 
            "method": "online_score",
            "token": "",
            "arguments": {}
        },
        {
            "account": "horns&hoofs",
            "login": "h&f",
            "method": "online_score", 
            "token": "invalid_token",
            "arguments": {}
        },
        {
            "account": "horns&hoofs",
            "login": "admin",
            "method": "online_score",
            "token": "",
            "arguments": {}
        },
        {
            "account": "test",
            "login": "test",
            "method": "online_score",
            "token": "wrong_token",
            "arguments": {}
        }
    ])
    def test_method_handler_bad_auth(self, request, case_index):
        """Тест плохой авторизации с разными кейсами"""
        response, code = method_handler({"body": request}, self.context, self.store)
        assert code == FORBIDDEN, f"Case {case_index} should return FORBIDDEN"
        assert response == "Forbidden", f"Case {case_index} should return 'Forbidden'"
    
    def test_method_handler_online_score_success(self):
        """Тест успешного вызова online_score"""
        # Создаем валидный токен
        digest = hashlib.sha512(("test_account" + "test_login" + SALT).encode('utf-8')).hexdigest()
        
        request = {
            "account": "test_account",
            "login": "test_login",
            "token": digest,
            "arguments": {
                "phone": "71234567890",
                "email": "test@example.com"
            },
            "method": "online_score"
        }
        
        response, code = method_handler({"body": request}, self.context, self.store)
        assert code == OK
        assert "score" in response
        assert response["score"] == 3.0
    
    def test_method_handler_online_score_admin(self):
        """Тест вызова online_score для админа"""
        # Создаем валидный токен для админа
        digest = hashlib.sha512((datetime.datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT).encode('utf-8')).hexdigest()
        
        request = {
            "account": "test",
            "login": ADMIN_LOGIN,
            "token": digest,
            "arguments": {
                "phone": "71234567890",
                "email": "test@example.com"
            },
            "method": "online_score"
        }
        
        response, code = method_handler({"body": request}, self.context, self.store)
        assert code == OK
        assert response["score"] == 42
    
    def test_method_handler_clients_interests_success(self):
        """Тест успешного вызова clients_interests"""
        # Создаем валидный токен
        digest = hashlib.sha512(("test_account" + "test_login" + SALT).encode('utf-8')).hexdigest()
        
        # Подготавливаем данные в хранилище
        self.store._storage["i:123"] = json.dumps(["books", "music"])
        self.store._storage["i:456"] = json.dumps(["sports"])
        
        request = {
            "account": "test_account",
            "login": "test_login",
            "token": digest,
            "arguments": {
                "client_ids": [123, 456, 789]
            },
            "method": "clients_interests"
        }
        
        response, code = method_handler({"body": request}, self.context, self.store)
        assert code == OK
        assert response["123"] == ["books", "music"]
        assert response["456"] == ["sports"]
        assert response["789"] == []
        assert self.context["nclients"] == 3


class TestCheckAuth:
    """Тесты для функции check_auth"""
    
    def test_check_auth_valid_user(self):
        """Тест валидной авторизации пользователя"""
        request = Mock()
        request.account = "test_account"
        request.login = "test_login"
        request.token = hashlib.sha512(("test_account" + "test_login" + SALT).encode('utf-8')).hexdigest()
        request.is_admin = False
        
        assert check_auth(request) is True
    
    def test_check_auth_invalid_user(self):
        """Тест невалидной авторизации пользователя"""
        request = Mock()
        request.account = "test_account"
        request.login = "test_login"
        request.token = "invalid_token"
        request.is_admin = False
        
        assert check_auth(request) is False
    
    def test_check_auth_admin(self):
        """Тест авторизации админа"""
        request = Mock()
        request.login = ADMIN_LOGIN
        request.is_admin = True
        
        # Создаем валидный токен для админа
        digest = hashlib.sha512((datetime.datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT).encode('utf-8')).hexdigest()
        request.token = digest
        
        assert check_auth(request) is True
    
    def test_check_auth_admin_invalid(self):
        """Тест невалидной авторизации админа"""
        request = Mock()
        request.login = ADMIN_LOGIN
        request.is_admin = True
        request.token = "invalid_token"
        
        assert check_auth(request) is False


class TestMethodRequest:
    """Тесты для MethodRequest"""
    
    def test_method_request_valid(self):
        """Тест валидного MethodRequest"""
        data = {
            "account": "test_account",
            "login": "test_login",
            "token": "test_token",
            "arguments": {"key": "value"},
            "method": "online_score"
        }
        
        request = MethodRequest(data)
        assert request.is_valid() is True
        assert request.account == "test_account"
        assert request.login == "test_login"
        assert request.token == "test_token"
        assert request.arguments == {"key": "value"}
        assert request.method == "online_score"
    
    def test_method_request_missing_required_fields(self):
        """Тест MethodRequest с отсутствующими обязательными полями"""
        data = {
            "account": "test_account",
            "token": "test_token",
            "arguments": {},
            "method": "online_score"
        }
        
        request = MethodRequest(data)
        assert request.is_valid() is False
        assert "login: Field is required" in request.errors
    
    def test_method_request_invalid_method(self):
        """Тест MethodRequest с невалидным методом"""
        data = {
            "account": "test_account",
            "login": "test_login",
            "token": "test_token",
            "arguments": {},
            "method": None  # method не может быть null
        }
        
        request = MethodRequest(data)
        assert request.is_valid() is False
        assert "method: Field is required" in request.errors
    
    def test_method_request_is_admin(self):
        """Тест свойства is_admin"""
        data = {
            "account": "test_account",
            "login": ADMIN_LOGIN,
            "token": "test_token",
            "arguments": {},
            "method": "online_score"
        }
        
        request = MethodRequest(data)
        assert request.is_admin is True
        
        data["login"] = "other_user"
        request = MethodRequest(data)
        assert request.is_admin is False


class TestOnlineScoreRequest:
    """Тесты для OnlineScoreRequest"""
    
    def test_online_score_request_valid(self):
        """Тест валидного OnlineScoreRequest"""
        data = {
            "phone": "71234567890",
            "email": "test@example.com",
            "first_name": "John",
            "last_name": "Doe"
        }
        
        request = OnlineScoreRequest(data)
        assert request.is_valid() is True
        assert request.phone == "71234567890"
        assert request.email == "test@example.com"
        assert request.first_name == "John"
        assert request.last_name == "Doe"
    
    def test_online_score_request_no_pairs(self):
        """Тест OnlineScoreRequest без пар полей"""
        data = {
            "phone": "71234567890",
            "first_name": "John"
            # Отсутствует email и last_name
        }
        
        request = OnlineScoreRequest(data)
        assert request.is_valid() is False
        assert "At least one pair" in request.errors[0]
    
    def test_online_score_request_invalid_email(self):
        """Тест OnlineScoreRequest с невалидным email"""
        data = {
            "phone": "71234567890",
            "email": "invalid_email",  # Нет @
            "first_name": "John",
            "last_name": "Doe"
        }
        
        request = OnlineScoreRequest(data)
        assert request.is_valid() is False
        assert "email: Email must contain @ symbol" in request.errors
    
    def test_online_score_request_invalid_phone(self):
        """Тест OnlineScoreRequest с невалидным телефоном"""
        data = {
            "phone": "123",  # Неправильный формат
            "email": "test@example.com",
            "first_name": "John",
            "last_name": "Doe"
        }
        
        request = OnlineScoreRequest(data)
        assert request.is_valid() is False
        assert "phone: Phone must be 11 digits long" in request.errors
    
    @cases([
        {
            "phone": "71234567890",
            "email": "test@example.com"
        },
        {
            "first_name": "John",
            "last_name": "Doe"
        },
        {
            "birthday": "01.01.1990",
            "gender": 1
        }
    ])
    def test_online_score_request_valid_pairs(self, data, case_index):
        """Тест валидных пар полей"""
        request = OnlineScoreRequest(data)
        assert request.is_valid() is True, f"Case {case_index} should be valid"


class TestClientsInterestsRequest:
    """Тесты для ClientsInterestsRequest"""
    
    def test_clients_interests_request_valid(self):
        """Тест валидного ClientsInterestsRequest"""
        data = {
            "client_ids": [123, 456, 789],
            "date": "01.01.2023"
        }
        
        request = ClientsInterestsRequest(data)
        assert request.is_valid() is True
        assert request.client_ids == [123, 456, 789]
        assert request.date == "01.01.2023"
    
    def test_clients_interests_request_missing_client_ids(self):
        """Тест ClientsInterestsRequest без client_ids"""
        data = {
            "date": "01.01.2023"
        }
        
        request = ClientsInterestsRequest(data)
        assert request.is_valid() is False
        assert "client_ids: Field is required" in request.errors
    
    def test_clients_interests_request_empty_client_ids(self):
        """Тест ClientsInterestsRequest с пустым client_ids"""
        data = {
            "client_ids": [],
            "date": "01.01.2023"
        }
        
        request = ClientsInterestsRequest(data)
        assert request.is_valid() is False
        assert "client_ids: Client IDs cannot be empty" in request.errors
    
    def test_clients_interests_request_invalid_client_ids(self):
        """Тест ClientsInterestsRequest с невалидными client_ids"""
        data = {
            "client_ids": [123, "456", 789],  # Строка вместо числа
            "date": "01.01.2023"
        }
        
        request = ClientsInterestsRequest(data)
        assert request.is_valid() is False
        assert "client_ids: All client IDs must be integers" in request.errors
    
    def test_clients_interests_request_invalid_date(self):
        """Тест ClientsInterestsRequest с невалидной датой"""
        data = {
            "client_ids": [123, 456],
            "date": "invalid_date"
        }
        
        request = ClientsInterestsRequest(data)
        assert request.is_valid() is False
        assert "date: Date must be in DD.MM.YYYY format" in request.errors


class TestFieldValidation:
    """Тесты валидации полей"""
    
    def test_char_field_validation(self):
        """Тест валидации CharField"""
        field = CharField(required=True, nullable=False)
        
        # Валидное значение
        assert field.validate("test") is True
        
        # Невалидные значения
        with pytest.raises(ValueError, match="Field is required"):
            field.validate(None)
        
        with pytest.raises(ValueError, match="Field must be a string"):
            field.validate(123)
    
    def test_email_field_validation(self):
        """Тест валидации EmailField"""
        field = EmailField(required=False, nullable=True)
        
        # Валидные значения
        assert field.validate("test@example.com") is True
        assert field.validate(None) is True
        
        # Невалидное значение
        with pytest.raises(ValueError, match="Email must contain @ symbol"):
            field.validate("invalid_email")
    
    def test_phone_field_validation(self):
        """Тест валидации PhoneField"""
        field = PhoneField(required=False, nullable=True)
        
        # Валидные значения
        assert field.validate("71234567890") is True
        assert field.validate(71234567890) is True  # int
        assert field.validate(None) is True
        
        # Невалидные значения
        with pytest.raises(ValueError, match="Phone must be 11 digits long"):
            field.validate("123")
        
        with pytest.raises(ValueError, match="Phone must start with 7"):
            field.validate("81234567890")
        
        with pytest.raises(ValueError, match="Phone must contain only digits"):
            field.validate("7123456789a")
    
    def test_date_field_validation(self):
        """Тест валидации DateField"""
        field = DateField(required=False, nullable=True)
        
        # Валидные значения
        assert field.validate("01.01.2023") is True
        assert field.validate(None) is True
        
        # Невалидные значения
        with pytest.raises(ValueError, match="Date must be in DD.MM.YYYY format"):
            field.validate("2023-01-01")
        
        with pytest.raises(ValueError, match="Date must be a string"):
            field.validate(123)
    
    def test_birthday_field_validation(self):
        """Тест валидации BirthDayField"""
        field = BirthDayField(required=False, nullable=True)
        
        # Валидные значения
        assert field.validate("01.01.1990") is True
        assert field.validate(None) is True
        
        # Невалидные значения
        with pytest.raises(ValueError, match="Age cannot be more than 70 years"):
            field.validate("01.01.1900")
    
    def test_gender_field_validation(self):
        """Тест валидации GenderField"""
        field = GenderField(required=False, nullable=True)
        
        # Валидные значения
        assert field.validate(0) is True
        assert field.validate(1) is True
        assert field.validate(2) is True
        assert field.validate(None) is True
        
        # Невалидные значения
        with pytest.raises(ValueError, match="Gender must be an integer"):
            field.validate("1")
        
        with pytest.raises(ValueError, match="Gender must be 0, 1 or 2"):
            field.validate(3)
    
    def test_client_ids_field_validation(self):
        """Тест валидации ClientIDsField"""
        field = ClientIDsField(required=True, nullable=False)
        
        # Валидные значения
        assert field.validate([123, 456]) is True
        
        # Невалидные значения
        with pytest.raises(ValueError, match="Field is required"):
            field.validate(None)
        
        with pytest.raises(ValueError, match="Client IDs must be a list"):
            field.validate("not_a_list")
        
        with pytest.raises(ValueError, match="Client IDs cannot be empty"):
            field.validate([])
        
        with pytest.raises(ValueError, match="All client IDs must be integers"):
            field.validate([123, "456"])
    
    def test_arguments_field_validation(self):
        """Тест валидации ArgumentsField"""
        field = ArgumentsField(required=True, nullable=False)
        
        # Валидные значения
        assert field.validate({"key": "value"}) is True
        
        # Невалидные значения
        with pytest.raises(ValueError, match="Field is required"):
            field.validate(None)
        
        with pytest.raises(ValueError, match="Field must be a dictionary"):
            field.validate("not_a_dict") 