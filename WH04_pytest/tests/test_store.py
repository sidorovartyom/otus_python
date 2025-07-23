#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
import time
import json
from unittest.mock import Mock, patch, MagicMock

from store import (
    MockStore, RedisStore, MemcacheStore, 
    StoreError, ConnectionError, TimeoutError,
    create_store, Store
)


class TestMockStore:
    """Тесты для MockStore"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.store = MockStore()
    
    def test_mock_store_basic_operations(self):
        """Тест базовых операций MockStore"""
        # Тест записи и чтения
        self.store._set("test_key", "test_value")
        assert self.store._get("test_key") == "test_value"
        
        # Тест кеша
        self.store.cache_set("cache_key", "cache_value", 3600)
        assert self.store.cache_get("cache_key") == "cache_value"
        
        # Тест персистентного хранилища
        self.store.get("persistent_key")
        assert self.store.get("persistent_key") is None  # Ключ не существует
    
    def test_mock_store_connection_errors(self):
        """Тест обработки ошибок подключения"""
        # Настраиваем ошибки подключения
        self.store.set_connection_errors(2)
        
        # Первые два вызова должны вызвать ошибку
        with pytest.raises(ConnectionError):
            self.store._get("test_key")
        
        with pytest.raises(ConnectionError):
            self.store._get("test_key")
        
        # Третий вызов должен пройти успешно
        result = self.store._get("test_key")
        assert result is None
    
    def test_mock_store_should_fail(self):
        """Тест флага should_fail"""
        self.store.set_should_fail(True)
        
        # Приватные методы должны вызывать ошибку
        with pytest.raises(ConnectionError):
            self.store._get("test_key")
        
        with pytest.raises(ConnectionError):
            self.store._set("test_key", "value")
        
        # Публичные методы должны возвращать None/False при ошибках
        assert self.store.cache_get("test_key") is None
        assert self.store.cache_set("test_key", "value", 3600) is False
    
    def test_mock_store_retry_logic(self):
        """Тест retry логики"""
        # Настраиваем 2 ошибки подключения
        self.store.set_connection_errors(2)
        
        # Операция должна пройти после retry
        result = self.store.get("test_key")
        assert result is None
    
    def test_mock_store_cache_operations(self):
        """Тест операций с кешем"""
        # Тест записи различных типов данных
        self.store.cache_set("str_key", "string_value", 3600)
        self.store.cache_set("int_key", 42, 3600)
        self.store.cache_set("dict_key", {"key": "value"}, 3600)
        self.store.cache_set("list_key", [1, 2, 3], 3600)
        
        # Проверяем, что все значения сохранились как строки
        assert self.store.cache_get("str_key") == "string_value"
        assert self.store.cache_get("int_key") == "42"
        assert self.store.cache_get("dict_key") == '{"key": "value"}'
        assert self.store.cache_get("list_key") == "[1, 2, 3]"
    
    def test_mock_store_clear(self):
        """Тест очистки хранилища"""
        # Заполняем хранилище
        self.store._storage["key1"] = "value1"
        self.store._cache["key2"] = "value2"
        
        # Очищаем
        self.store.clear()
        
        # Проверяем, что все очистилось
        assert len(self.store._storage) == 0
        assert len(self.store._cache) == 0
    
    def test_mock_store_error_handling(self):
        """Тест обработки ошибок в публичных методах"""
        self.store.set_should_fail(True)
        
        # Публичные методы должны возвращать None/False при ошибках
        assert self.store.get("test_key") is None
        assert self.store.cache_get("test_key") is None
        assert self.store.cache_set("test_key", "value", 3600) is False


class TestBaseStoreRetryLogic:
    """Тесты retry логики базового класса"""
    
    def test_retry_success_on_first_attempt(self):
        """Тест успешного выполнения с первой попытки"""
        store = MockStore(max_retries=3)
        
        result = store._retry_operation(lambda x: x * 2, 5)
        assert result == 10
    
    def test_retry_success_after_failures(self):
        """Тест успешного выполнения после неудач"""
        store = MockStore(max_retries=3)
        
        # Создаем функцию, которая падает 2 раза, а потом успешна
        call_count = 0
        def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise ConnectionError("Connection failed")
            return "success"
        
        result = store._retry_operation(failing_function)
        assert result == "success"
        assert call_count == 3
    
    def test_retry_all_attempts_fail(self):
        """Тест неудачи всех попыток"""
        store = MockStore(max_retries=3)
        
        def always_failing_function():
            raise ConnectionError("Always fails")
        
        with pytest.raises(ConnectionError):
            store._retry_operation(always_failing_function)
    
    def test_retry_with_different_exceptions(self):
        """Тест retry с разными типами исключений"""
        store = MockStore(max_retries=3)
        
        call_count = 0
        def mixed_failing_function():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionError("Connection error")
            elif call_count == 2:
                raise TimeoutError("Timeout error")
            else:
                return "success"
        
        result = store._retry_operation(mixed_failing_function)
        assert result == "success"
    
    def test_retry_with_unexpected_exception(self):
        """Тест retry с неожиданным исключением"""
        store = MockStore(max_retries=3)
        
        def unexpected_failing_function():
            raise ValueError("Unexpected error")
        
        with pytest.raises(ValueError):
            store._retry_operation(unexpected_failing_function)


class TestRedisStore:
    """Тесты для RedisStore"""
    
    @patch('store.REDIS_AVAILABLE', True)
    @patch('store.redis', create=True)
    def test_redis_store_initialization(self, mock_redis):
        """Тест инициализации RedisStore"""
        mock_redis.Redis.return_value = Mock()
        
        store = RedisStore(host='testhost', port=6380, db=1)
        
        mock_redis.Redis.assert_called_once_with(
            host='testhost',
            port=6380,
            db=1,
            socket_timeout=1.0,
            socket_connect_timeout=1.0,
            retry_on_timeout=True,
            health_check_interval=30
        )
    
    @patch('store.REDIS_AVAILABLE', False)
    def test_redis_store_import_error(self):
        """Тест ошибки импорта Redis"""
        with pytest.raises(ImportError):
            RedisStore()
    
    @patch('store.REDIS_AVAILABLE', True)
    @patch('store.redis', create=True)
    def test_redis_store_get_success(self, mock_redis):
        """Тест успешного получения данных из Redis"""
        mock_client = Mock()
        mock_client.get.return_value = b"test_value"
        mock_redis.Redis.return_value = mock_client
        
        store = RedisStore()
        result = store._get("test_key")
        
        assert result == "test_value"
        mock_client.get.assert_called_once_with("test_key")
    
    @patch('store.REDIS_AVAILABLE', True)
    @patch('store.redis', create=True)
    def test_redis_store_get_none(self, mock_redis):
        """Тест получения None из Redis"""
        mock_client = Mock()
        mock_client.get.return_value = None
        mock_redis.Redis.return_value = mock_client
        
        store = RedisStore()
        result = store._get("test_key")
        
        assert result is None
    
    @patch('store.REDIS_AVAILABLE', True)
    @patch('store.redis', create=True)
    def test_redis_store_get_connection_error(self, mock_redis):
        """Тест ошибки подключения к Redis"""
        mock_client = Mock()
        # Создаем правильный тип исключения
        mock_redis.ConnectionError = type('ConnectionError', (Exception,), {})
        mock_client.get.side_effect = mock_redis.ConnectionError("Connection failed")
        mock_redis.Redis.return_value = mock_client
        
        store = RedisStore()
        
        with pytest.raises(ConnectionError):
            store._get("test_key")
    
    @patch('store.REDIS_AVAILABLE', True)
    @patch('store.redis', create=True)
    def test_redis_store_set_with_ttl(self, mock_redis):
        """Тест записи в Redis с TTL"""
        mock_client = Mock()
        mock_client.setex.return_value = True
        mock_redis.Redis.return_value = mock_client
        
        store = RedisStore()
        result = store._set("test_key", "test_value", 3600)
        
        assert result is True
        mock_client.setex.assert_called_once_with("test_key", 3600, "test_value")
    
    @patch('store.REDIS_AVAILABLE', True)
    @patch('store.redis', create=True)
    def test_redis_store_set_without_ttl(self, mock_redis):
        """Тест записи в Redis без TTL"""
        mock_client = Mock()
        mock_client.set.return_value = True
        mock_redis.Redis.return_value = mock_client
        
        store = RedisStore()
        result = store._set("test_key", "test_value")
        
        assert result is True
        mock_client.set.assert_called_once_with("test_key", "test_value")


class TestMemcacheStore:
    """Тесты для MemcacheStore"""
    
    @patch('store.MEMCACHE_AVAILABLE', True)
    @patch('store.memcache', create=True)
    def test_memcache_store_initialization(self, mock_memcache):
        """Тест инициализации MemcacheStore"""
        mock_client = Mock()
        mock_memcache.Client.return_value = mock_client
        
        store = MemcacheStore(servers=['localhost:11211'])
        
        mock_memcache.Client.assert_called_once_with(['localhost:11211'], debug=0)
    
    @patch('store.MEMCACHE_AVAILABLE', False)
    def test_memcache_store_import_error(self):
        """Тест ошибки импорта Memcached"""
        with pytest.raises(ImportError):
            MemcacheStore()
    
    @patch('store.MEMCACHE_AVAILABLE', True)
    @patch('store.memcache', create=True)
    def test_memcache_store_get_success(self, mock_memcache):
        """Тест успешного получения данных из Memcached"""
        mock_client = Mock()
        mock_client.get.return_value = "test_value"
        mock_memcache.Client.return_value = mock_client
        
        store = MemcacheStore()
        result = store._get("test_key")
        
        assert result == "test_value"
        mock_client.get.assert_called_once_with("test_key")
    
    @patch('store.MEMCACHE_AVAILABLE', True)
    @patch('store.memcache', create=True)
    def test_memcache_store_set_success(self, mock_memcache):
        """Тест успешной записи в Memcached"""
        mock_client = Mock()
        mock_client.set.return_value = True
        mock_memcache.Client.return_value = mock_client
        
        store = MemcacheStore()
        result = store._set("test_key", "test_value", 3600)
        
        assert result is True
        mock_client.set.assert_called_once_with("test_key", "test_value", time=3600)


class TestStoreFactory:
    """Тесты фабрики хранилищ"""
    
    def test_create_store_mock(self):
        """Тест создания MockStore"""
        store = create_store('mock')
        assert isinstance(store, MockStore)
    
    @patch('store.REDIS_AVAILABLE', True)
    @patch('store.redis', create=True)
    def test_create_store_redis(self, mock_redis):
        """Тест создания RedisStore"""
        mock_redis.Redis.return_value = Mock()
        
        store = create_store('redis', host='testhost', port=6380)
        assert isinstance(store, RedisStore)
    
    @patch('store.MEMCACHE_AVAILABLE', True)
    @patch('store.memcache', create=True)
    def test_create_store_memcache(self, mock_memcache):
        """Тест создания MemcacheStore"""
        mock_memcache.Client.return_value = Mock()
        
        store = create_store('memcache', servers=['localhost:11211'])
        assert isinstance(store, MemcacheStore)
    
    def test_create_store_unknown_type(self):
        """Тест создания неизвестного типа хранилища"""
        with pytest.raises(ValueError):
            create_store('unknown_type')


class TestStoreWrapper:
    """Тесты для класса Store (обертка)"""
    
    def test_store_wrapper_basic_operations(self):
        """Тест базовых операций Store wrapper"""
        store = Store('mock')
        
        # Тест записи в кеш
        result = store.cache_set("test_key", "test_value", 3600)
        assert result is True
        
        # Тест чтения из кеша
        value = store.cache_get("test_key")
        assert value == "test_value"
        
        # Тест чтения из хранилища
        value = store.get("test_key")
        assert value is None  # Ключ не существует в хранилище
    
    @patch('store.create_store')
    def test_store_wrapper_initialization(self, mock_create_store):
        """Тест инициализации Store wrapper"""
        mock_store = Mock()
        mock_create_store.return_value = mock_store
        
        store = Store('redis', host='localhost', port=6379)
        
        mock_create_store.assert_called_once_with('redis', host='localhost', port=6379)


class TestStoreErrorHandling:
    """Тесты обработки ошибок хранилища"""
    
    def test_store_error_inheritance(self):
        """Тест иерархии исключений"""
        assert issubclass(ConnectionError, StoreError)
        assert issubclass(TimeoutError, StoreError)
    
    def test_store_error_messages(self):
        """Тест сообщений об ошибках"""
        conn_error = ConnectionError("Connection failed")
        timeout_error = TimeoutError("Operation timed out")
        
        assert str(conn_error) == "Connection failed"
        assert str(timeout_error) == "Operation timed out" 